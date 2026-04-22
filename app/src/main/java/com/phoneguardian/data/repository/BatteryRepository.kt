package com.phoneguardian.data.repository

import com.phoneguardian.PhoneGuardianApp
import com.phoneguardian.data.local.entity.BatteryEvent
import com.phoneguardian.data.local.entity.ChargeCycle
import kotlinx.coroutines.flow.Flow

class BatteryRepository {

    private val batteryEventDao = PhoneGuardianApp.instance.database.batteryEventDao()
    private val chargeCycleDao = PhoneGuardianApp.instance.database.chargeCycleDao()

    suspend fun saveBatteryEvent(level: Int, isCharging: Boolean, chargeType: Int) {
        val event = BatteryEvent(
            timestamp = System.currentTimeMillis(),
            level = level,
            isCharging = isCharging,
            chargeType = chargeType
        )
        batteryEventDao.insert(event)
    }

    suspend fun startChargeCycle(level: Int): Long {
        val cycle = ChargeCycle(
            startTime = System.currentTimeMillis(),
            endTime = null,
            startLevel = level,
            endLevel = null,
            screenMsDuringCharge = 0,
            date = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.getDefault())
                .format(java.util.Date())
        )
        return chargeCycleDao.insert(cycle)
    }

    suspend fun endChargeCycle(endLevel: Int, screenMsDuringCharge: Long): ChargeCycle? {
        val activeCycle = chargeCycleDao.getActiveCycle() ?: return null
        val updatedCycle = activeCycle.copy(
            endTime = System.currentTimeMillis(),
            endLevel = endLevel,
            screenMsDuringCharge = screenMsDuringCharge
        )
        chargeCycleDao.update(updatedCycle)
        return updatedCycle
    }

    suspend fun getActiveCycle(): ChargeCycle? {
        return chargeCycleDao.getActiveCycle()
    }

    suspend fun updateActiveCycleScreenTime(screenMs: Long) {
        val activeCycle = chargeCycleDao.getActiveCycle() ?: return
        val updatedCycle = activeCycle.copy(
            screenMsDuringCharge = activeCycle.screenMsDuringCharge + screenMs
        )
        chargeCycleDao.update(updatedCycle)
    }

    fun getTodayEvents(): Flow<List<BatteryEvent>> {
        val startOfDay = getStartOfDay()
        return batteryEventDao.getTodayEvents(startOfDay)
    }

    fun getLatestEvent(): Flow<BatteryEvent?> {
        return batteryEventDao.getLatestEvent()
    }

    fun getRecentCycles(limit: Int): Flow<List<ChargeCycle>> {
        return chargeCycleDao.getRecentCycles(limit)
    }

    fun getCyclesByDate(date: String): Flow<List<ChargeCycle>> {
        return chargeCycleDao.getCyclesByDate(date)
    }

    suspend fun deleteOldBatteryEvents(retentionDays: Int) {
        val beforeTime = System.currentTimeMillis() - retentionDays * 24 * 60 * 60 * 1000L
        batteryEventDao.deleteOldData(beforeTime)
    }

    suspend fun deleteOldChargeCycles(retentionDays: Int) {
        val beforeTime = System.currentTimeMillis() - retentionDays * 24 * 60 * 60 * 1000L
        chargeCycleDao.deleteOldData(beforeTime)
    }

    private fun getStartOfDay(): Long {
        val calendar = java.util.Calendar.getInstance()
        calendar.set(java.util.Calendar.HOUR_OF_DAY, 0)
        calendar.set(java.util.Calendar.MINUTE, 0)
        calendar.set(java.util.Calendar.SECOND, 0)
        calendar.set(java.util.Calendar.MILLISECOND, 0)
        return calendar.timeInMillis
    }
}
