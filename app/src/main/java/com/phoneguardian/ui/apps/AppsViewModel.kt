package com.phoneguardian.ui.apps

import android.app.Application
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.phoneguardian.data.repository.BatteryRepository
import com.phoneguardian.data.repository.UsageRepository
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class AppInfo(
    val name: String,
    val duration: Long,
    val packageName: String = ""
)

data class AppsUiState(
    val topApps: List<AppInfo> = emptyList(),
    val recentChargeCycles: List<ChargeCycleInfo> = emptyList()
)

data class ChargeCycleInfo(
    val date: String,
    val duration: String,
    val screenTimeDuringCharge: String,
    val startLevel: Int,
    val endLevel: Int?
)

class AppsViewModel(application: Application) : AndroidViewModel(application) {

    private val usageRepository = UsageRepository()
    private val batteryRepository = BatteryRepository()

    private val _uiState = MutableStateFlow(AppsUiState())
    val uiState: StateFlow<AppsUiState> = _uiState.asStateFlow()

    init {
        loadAppsData()
    }

    private fun loadAppsData() {
        viewModelScope.launch {
            try {
                val topApps = usageRepository.getTopAppsToday(20)
                val appInfoList = topApps.map { (name, ms) ->
                    AppInfo(name = name, duration = ms)
                }
                _uiState.value = _uiState.value.copy(topApps = appInfoList)
            } catch (e: Exception) {
                // 可能没有授权
            }
        }

        viewModelScope.launch {
            batteryRepository.getRecentCycles(5).collect { cycles ->
                val cycleInfoList = cycles.map { cycle ->
                    ChargeCycleInfo(
                        date = TimeUtils.formatDate(cycle.startTime),
                        duration = TimeUtils.formatDuration(cycle.endTime?.minus(cycle.startTime) ?: 0),
                        screenTimeDuringCharge = TimeUtils.formatDuration(cycle.screenMsDuringCharge),
                        startLevel = cycle.startLevel,
                        endLevel = cycle.endLevel
                    )
                }
                _uiState.value = _uiState.value.copy(recentChargeCycles = cycleInfoList)
            }
        }
    }

    fun refresh() {
        loadAppsData()
    }
}
