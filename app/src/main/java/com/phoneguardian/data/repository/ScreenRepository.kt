package com.phoneguardian.data.repository

import com.phoneguardian.PhoneGuardianApp
import com.phoneguardian.data.local.entity.ScreenSession
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.flow.Flow

class ScreenRepository {

    private val dao = PhoneGuardianApp.instance.database.screenSessionDao()

    suspend fun saveSession(startTime: Long, endTime: Long) {
        val duration = endTime - startTime
        val date = TimeUtils.formatDate(startTime)
        val session = ScreenSession(
            startTime = startTime,
            endTime = endTime,
            durationMs = duration,
            date = date
        )
        dao.insert(session)
    }

    fun getSessionsByDate(date: String): Flow<List<ScreenSession>> {
        return dao.getSessionsByDate(date)
    }

    fun getSessionsBetween(startDate: String, endDate: String): Flow<List<ScreenSession>> {
        return dao.getSessionsBetween(startDate, endDate)
    }

    fun getTotalDurationByDate(date: String): Flow<Long?> {
        return dao.getTotalDurationByDate(date)
    }

    suspend fun deleteOldData(retentionDays: Int) {
        val beforeDate = TimeUtils.getDateBeforeDays(retentionDays)
        dao.deleteOldData(beforeDate)
    }
}
