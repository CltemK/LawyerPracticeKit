package com.phoneguardian.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import com.phoneguardian.data.local.entity.ScreenSession
import kotlinx.coroutines.flow.Flow

@Dao
interface ScreenSessionDao {

    @Insert
    suspend fun insert(session: ScreenSession): Long

    @Query("SELECT * FROM screen_sessions WHERE date = :date ORDER BY startTime DESC")
    fun getSessionsByDate(date: String): Flow<List<ScreenSession>>

    @Query("SELECT * FROM screen_sessions WHERE date BETWEEN :startDate AND :endDate ORDER BY startTime DESC")
    fun getSessionsBetween(startDate: String, endDate: String): Flow<List<ScreenSession>>

    @Query("SELECT SUM(durationMs) FROM screen_sessions WHERE date = :date")
    fun getTotalDurationByDate(date: String): Flow<Long?>

    @Query("DELETE FROM screen_sessions WHERE date < :beforeDate")
    suspend fun deleteOldData(beforeDate: String)

    @Query("SELECT COUNT(*) FROM screen_sessions WHERE date = :date")
    suspend fun getSessionCountByDate(date: String): Int
}
