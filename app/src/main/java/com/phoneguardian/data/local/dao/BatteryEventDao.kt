package com.phoneguardian.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Update
import com.phoneguardian.data.local.entity.BatteryEvent
import kotlinx.coroutines.flow.Flow

@Dao
interface BatteryEventDao {

    @Insert
    suspend fun insert(event: BatteryEvent): Long

    @Query("SELECT * FROM battery_events WHERE timestamp BETWEEN :startTime AND :endTime ORDER BY timestamp ASC")
    fun getEventsBetween(startTime: Long, endTime: Long): Flow<List<BatteryEvent>>

    @Query("SELECT * FROM battery_events ORDER BY timestamp DESC LIMIT 1")
    fun getLatestEvent(): Flow<BatteryEvent?>

    @Query("SELECT * FROM battery_events WHERE timestamp >= :startOfDay ORDER BY timestamp ASC")
    fun getTodayEvents(startOfDay: Long): Flow<List<BatteryEvent>>

    @Query("DELETE FROM battery_events WHERE timestamp < :beforeTime")
    suspend fun deleteOldData(beforeTime: Long)
}
