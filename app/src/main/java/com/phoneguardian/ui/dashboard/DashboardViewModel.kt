package com.phoneguardian.ui.dashboard

import android.app.Application
import android.app.usage.UsageStatsManager
import android.content.Context
import android.os.BatteryManager
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
        // 直接读取当前电池状态
        readBatteryDirectly()

        // 读取今日亮屏时长（从数据库 + UsageStatsManager 估算）
        loadTodayScreenTime()

        viewModelScope.launch {
            // 获取今日电池曲线
            batteryRepository.getTodayEvents().collect { events ->
                _uiState.value = _uiState.value.copy(batteryCurve = events)
            }
        }

        viewModelScope.launch {
            // 获取最新电池事件（补充实时状态）
            batteryRepository.getLatestEvent().collect { event ->
                if (event != null) {
                    _uiState.value = _uiState.value.copy(
                        currentBattery = event.level,
                        isCharging = event.isCharging
                    )
                }
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
            // 获取 TOP 3 应用（直接显示应用名）
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

    private fun readBatteryDirectly() {
        val context = getApplication<Application>()
        val batteryManager = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val level = batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        val isCharging = batteryManager.isCharging

        _uiState.value = _uiState.value.copy(
            currentBattery = level,
            isCharging = isCharging
        )
    }

    private fun loadTodayScreenTime() {
        viewModelScope.launch {
            val today = TimeUtils.getTodayString()

            // 从数据库获取已记录的亮屏时长
            screenRepository.getTotalDurationByDate(today).collect { dbDuration ->
                // 同时从 UsageStatsManager 获取前台总时长作为补充
                val usageStatsDuration = getUsageStatsScreenTime()
                val total = maxOf(dbDuration ?: 0L, usageStatsDuration)
                _uiState.value = _uiState.value.copy(todayScreenTime = total)
            }
        }
    }

    private fun getUsageStatsScreenTime(): Long {
        val context = getApplication<Application>()
        val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val startOfDay = TimeUtils.getStartOfDay()
        val now = System.currentTimeMillis()

        val stats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startOfDay,
            now
        ) ?: return 0L

        return stats
            .filter { it.totalTimeInForeground > 0 }
            .sumOf { it.totalTimeInForeground }
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

        val isGood = summary.sleepScreenMs < 30 * 60 * 1000

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
