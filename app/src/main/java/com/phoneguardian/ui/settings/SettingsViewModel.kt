package com.phoneguardian.ui.settings

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.phoneguardian.data.datastore.SettingsDataStore
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class SettingsUiState(
    val sleepStartTime: String = SettingsDataStore.DEFAULT_SLEEP_START,
    val sleepEndTime: String = SettingsDataStore.DEFAULT_SLEEP_END,
    val dataRetentionDays: Int = SettingsDataStore.DEFAULT_RETENTION_DAYS,
    val notificationEnabled: Boolean = true
)

class SettingsViewModel(application: Application) : AndroidViewModel(application) {

    private val settingsDataStore = SettingsDataStore(application)

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        loadSettings()
    }

    private fun loadSettings() {
        viewModelScope.launch {
            settingsDataStore.sleepStartTime.collect { time ->
                _uiState.value = _uiState.value.copy(sleepStartTime = time)
            }
        }
        viewModelScope.launch {
            settingsDataStore.sleepEndTime.collect { time ->
                _uiState.value = _uiState.value.copy(sleepEndTime = time)
            }
        }
        viewModelScope.launch {
            settingsDataStore.dataRetentionDays.collect { days ->
                _uiState.value = _uiState.value.copy(dataRetentionDays = days)
            }
        }
        viewModelScope.launch {
            settingsDataStore.notificationEnabled.collect { enabled ->
                _uiState.value = _uiState.value.copy(notificationEnabled = enabled)
            }
        }
    }

    fun setSleepStartTime(time: String) {
        viewModelScope.launch {
            settingsDataStore.setSleepStartTime(time)
        }
    }

    fun setSleepEndTime(time: String) {
        viewModelScope.launch {
            settingsDataStore.setSleepEndTime(time)
        }
    }

    fun setDataRetentionDays(days: Int) {
        viewModelScope.launch {
            settingsDataStore.setDataRetentionDays(days)
        }
    }

    fun setNotificationEnabled(enabled: Boolean) {
        viewModelScope.launch {
            settingsDataStore.setNotificationEnabled(enabled)
        }
    }
}
