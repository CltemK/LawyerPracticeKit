package com.phoneguardian.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.phoneguardian.data.local.entity.DailySummary
import kotlinx.coroutines.flow.Flow

@Dao
interface DailySummaryDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(summary: DailySummary)

    @Query("SELECT * FROM daily_summary WHERE date = :date")
    fun getSummaryByDate(date: String): Flow<DailySummary?>

    @Query("SELECT * FROM daily_summary WHERE date BETWEEN :startDate AND :endDate ORDER BY date DESC")
    fun getSummariesBetween(startDate: String, endDate: String): Flow<List<DailySummary>>

    @Query("SELECT * FROM daily_summary ORDER BY date DESC LIMIT :limit")
    fun getRecentSummaries(limit: Int): Flow<List<DailySummary>>

    @Query("DELETE FROM daily_summary WHERE date < :beforeDate")
    suspend fun deleteOldData(beforeDate: String)
}
