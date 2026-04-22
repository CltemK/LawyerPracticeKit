package com.phoneguardian.ui.dashboard

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.phoneguardian.data.datastore.SettingsDataStore
import com.phoneguardian.data.local.entity.BatteryEvent
import com.phoneguardian.data.local.entity.DailySummary
import com.phoneguardian.data.repository.BatteryRepository
import com.phoneguardian.data.repository.ScreenRepository
import com.phoneguardian.data.repository.UsageRepository
import com.phoneguardian.util.SleepAnalyzer
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

data class DashboardUiState(
    val todayScreenTime: Long = 0,
    val sleepStatus: SleepStatus = SleepStatus(),
    val currentBattery: Int = 0,
    val isCharging: Boolean = false,
    val batteryCurve: List<BatteryEvent> = emptyList(),
    val topApps: List<AppUsage> = emptyList()
)

data class SleepStatus(
    val isGood: Boolean = false,
    val lastNightSleep: Long = 0,
    val message: String = "正在分析..."
)

data class AppUsage(
    val name: String,
    val duration: Long
)

class DashboardViewModel(application: Application) : AndroidViewModel(application) {

    private val screenRepository = ScreenRepository()
    private val batteryRepository = BatteryRepository()
    private val usageRepository = UsageRepository()
    private val settingsDataStore = SettingsDataStore(application)

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        loadDashboardData()
    }

    private fun loadDashboardData() {
        viewModelScope.launch {
            val today = TimeUtils.getTodayString()

            // 获取今日亮屏时长
            screenRepository.getTotalDurationByDate(today).collect { duration ->
                _uiState.value = _uiState.value.copy(todayScreenTime = duration ?: 0)
            }
        }

        viewModelScope.launch {
            // 获取最新电池状态
            batteryRepository.getLatestEvent().collect { event ->
                _uiState.value = _uiState.value.copy(
                    currentBattery = event?.level ?: 0,
                    isCharging = event?.isCharging ?: false
                )
            }
        }

        viewModelScope.launch {
            // 获取今日电池曲线
            batteryRepository.getTodayEvents().collect { events ->
                _uiState.value = _uiState.value.copy(batteryCurve = events)
            }
        }

        viewModelScope.launch {
            // 获取昨日睡眠状态
            val yesterday = TimeUtils.getYesterdayString()
            usageRepository.getDailySummary(yesterday).collect { summary ->
                val sleepStatus = analyzeSleepStatus(summary)
                _uiState.value = _uiState.value.copy(sleepStatus = sleepStatus)
            }
        }

        viewModelScope.launch {
            // 获取 TOP 3 应用
            try {
                val topApps = usageRepository.getTopAppsToday(3)
                val appUsageList = topApps.map { (name, ms) ->
                    AppUsage(name = name, duration = ms)
                }
                _uiState.value = _uiState.value.copy(topApps = appUsageList)
            } catch (e: Exception) {
                // 可能没有授权 UsageStats
            }
        }
    }

    private suspend fun analyzeSleepStatus(summary: DailySummary?): SleepStatus {
        if (summary == null) {
            return SleepStatus(isGood = true, lastNightSleep = 0, message = "暂无数据")
        }

        val sleepStartTime = settingsDataStore.sleepStartTime.first()
        val sleepEndTime = settingsDataStore.sleepEndTime.first()
        val (startHour, startMinute) = TimeUtils.parseTime(sleepStartTime)
        val (endHour, endMinute) = TimeUtils.parseTime(sleepEndTime)

        val sleepAnalyzer = SleepAnalyzer(startHour, startMinute, endHour, endMinute)
        val (sleepStart, sleepEnd) = sleepAnalyzer.getSleepPeriodForDate(TimeUtils.getTodayString())

        val expectedSleepDuration = sleepEnd - sleepStart
        val actualSleepDuration = expectedSleepDuration - summary.sleepScreenMs

        val isGood = summary.sleepScreenMs < 30 * 60 * 1000 // 睡眠时段使用少于30分钟算良好

        val message = when {
            summary.sleepScreenMs == 0L -> "昨晚睡眠充足 ✓"
            summary.sleepScreenMs < 30 * 60 * 1000 -> "昨晚有小段时间使用手机"
            summary.sleepScreenMs < 60 * 60 * 1000 -> "昨晚有段时间在熬夜使用"
            else -> "昨晚长时间熬夜使用手机！"
        }

        return SleepStatus(
            isGood = isGood,
            lastNightSleep = actualSleepDuration,
            message = message
        )
    }

    fun refresh() {
        loadDashboardData()
    }
}
