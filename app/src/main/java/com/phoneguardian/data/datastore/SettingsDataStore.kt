package com.phoneguardian.data.datastore

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

class SettingsDataStore(private val context: Context) {

    companion object {
        val SLEEP_START_TIME = stringPreferencesKey("sleep_start_time")
        val SLEEP_END_TIME = stringPreferencesKey("sleep_end_time")
        val DATA_RETENTION_DAYS = intPreferencesKey("data_retention_days")
        val NOTIFICATION_ENABLED = booleanPreferencesKey("notification_enabled")

        const val DEFAULT_SLEEP_START = "22:00"
        const val DEFAULT_SLEEP_END = "07:00"
        const val DEFAULT_RETENTION_DAYS = 90
    }

    val sleepStartTime: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[SLEEP_START_TIME] ?: DEFAULT_SLEEP_START
    }

    val sleepEndTime: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[SLEEP_END_TIME] ?: DEFAULT_SLEEP_END
    }

    val dataRetentionDays: Flow<Int> = context.dataStore.data.map { preferences ->
        preferences[DATA_RETENTION_DAYS] ?: DEFAULT_RETENTION_DAYS
    }

    val notificationEnabled: Flow<Boolean> = context.dataStore.data.map { preferences ->
        preferences[NOTIFICATION_ENABLED] ?: true
    }

    suspend fun setSleepStartTime(time: String) {
        context.dataStore.edit { preferences ->
            preferences[SLEEP_START_TIME] = time
        }
    }

    suspend fun setSleepEndTime(time: String) {
        context.dataStore.edit { preferences ->
            preferences[SLEEP_END_TIME] = time
        }
    }

    suspend fun setDataRetentionDays(days: Int) {
        context.dataStore.edit { preferences ->
            preferences[DATA_RETENTION_DAYS] = days
        }
    }

    suspend fun setNotificationEnabled(enabled: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[NOTIFICATION_ENABLED] = enabled
        }
    }
}
