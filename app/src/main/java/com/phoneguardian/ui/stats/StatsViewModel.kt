package com.phoneguardian.ui.stats

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.phoneguardian.data.datastore.SettingsDataStore
import com.phoneguardian.data.local.entity.DailySummary
import com.phoneguardian.data.repository.UsageRepository
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class StatsPeriod {
    TODAY, WEEK, MONTH
}

data class StatsUiState(
    val period: StatsPeriod = StatsPeriod.TODAY,
    val summaries: List<DailySummary> = emptyList(),
    val totalScreenTime: Long = 0,
    val totalSleepScreenTime: Long = 0
)

class StatsViewModel(application: Application) : AndroidViewModel(application) {

    private val usageRepository = UsageRepository()
    private val settingsDataStore = SettingsDataStore(application)

    private val _uiState = MutableStateFlow(StatsUiState())
    val uiState: StateFlow<StatsUiState> = _uiState.asStateFlow()

    init {
        loadStats(StatsPeriod.WEEK)
    }

    fun loadStats(period: StatsPeriod) {
        _uiState.value = _uiState.value.copy(period = period)

        viewModelScope.launch {
            val (startDate, endDate) = when (period) {
                StatsPeriod.TODAY -> {
                    val today = TimeUtils.getTodayString()
                    Pair(today, today)
                }
                StatsPeriod.WEEK -> {
                    val dates = TimeUtils.getWeekDates()
                    val today = TimeUtils.getTodayString()
                    Pair(dates.firstOrNull() ?: today, dates.lastOrNull() ?: today)
                }
                StatsPeriod.MONTH -> {
                    val calendar = java.util.Calendar.getInstance()
                    val endDate = TimeUtils.getTodayString()
                    calendar.add(java.util.Calendar.MONTH, -1)
                    val startDate = TimeUtils.formatDate(calendar.timeInMillis)
                    Pair(startDate, endDate)
                }
            }

            usageRepository.getSummariesBetween(startDate, endDate).collect { summaries ->
                val totalScreenTime = summaries.sumOf { it.totalScreenMs }
                val totalSleepScreenTime = summaries.sumOf { it.sleepScreenMs }

                _uiState.value = _uiState.value.copy(
                    summaries = summaries,
                    totalScreenTime = totalScreenTime,
                    totalSleepScreenTime = totalSleepScreenTime
                )
            }
        }
    }

    fun setPeriod(period: StatsPeriod) {
        loadStats(period)
    }
}
