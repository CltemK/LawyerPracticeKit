package com.phoneguardian.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Update
import com.phoneguardian.data.local.entity.ChargeCycle
import kotlinx.coroutines.flow.Flow

@Dao
interface ChargeCycleDao {

    @Insert
    suspend fun insert(cycle: ChargeCycle): Long

    @Update
    suspend fun update(cycle: ChargeCycle)

    @Query("SELECT * FROM charge_cycles WHERE endTime IS NULL ORDER BY startTime DESC LIMIT 1")
    suspend fun getActiveCycle(): ChargeCycle?

    @Query("SELECT * FROM charge_cycles ORDER BY startTime DESC LIMIT :limit")
    fun getRecentCycles(limit: Int): Flow<List<ChargeCycle>>

    @Query("SELECT * FROM charge_cycles WHERE date = :date ORDER BY startTime DESC")
    fun getCyclesByDate(date: String): Flow<List<ChargeCycle>>

    @Query("DELETE FROM charge_cycles WHERE startTime < :beforeTime")
    suspend fun deleteOldData(beforeTime: Long)
}
