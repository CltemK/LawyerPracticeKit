package com.phoneguardian.data.repository

import android.app.usage.UsageStats
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.pm.PackageManager
import com.phoneguardian.PhoneGuardianApp
import com.phoneguardian.data.local.dao.DailySummaryDao
import com.phoneguardian.data.local.entity.DailySummary
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.flow.Flow

class UsageRepository {

    private val dailySummaryDao = PhoneGuardianApp.instance.database.dailySummaryDao()
    private val context: Context = PhoneGuardianApp.instance

    fun getDailySummary(date: String): Flow<DailySummary?> {
        return dailySummaryDao.getSummaryByDate(date)
    }

    fun getSummariesBetween(startDate: String, endDate: String): Flow<List<DailySummary>> {
        return dailySummaryDao.getSummariesBetween(startDate, endDate)
    }

    fun getRecentSummaries(limit: Int): Flow<List<DailySummary>> {
        return dailySummaryDao.getRecentSummaries(limit)
    }

    suspend fun saveDailySummary(summary: DailySummary) {
        dailySummaryDao.insert(summary)
    }

    suspend fun deleteOldSummaries(retentionDays: Int) {
        val beforeDate = TimeUtils.getDateBeforeDays(retentionDays)
        dailySummaryDao.deleteOldData(beforeDate)
    }

    fun getTopAppsToday(limit: Int = 3): List<Pair<String, Long>> {
        val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val startOfDay = TimeUtils.getStartOfDay()
        val endOfDay = System.currentTimeMillis()

        val usageStats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startOfDay,
            endOfDay
        )

        return usageStats
            ?.filter { it.totalTimeInForeground > 0 }
            ?.sortedByDescending { it.totalTimeInForeground }
            ?.take(limit)
            ?.map { stat ->
                val appName = getAppName(stat.packageName)
                Pair(appName, stat.totalTimeInForeground)
            }
            ?: emptyList()
    }

    fun getAppsForPeriod(startTime: Long, endTime: Long, limit: Int = 10): List<Pair<String, Long>> {
        val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager

        val usageStats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startTime,
            endTime
        )

        return usageStats
            ?.filter { it.totalTimeInForeground > 0 }
            ?.sortedByDescending { it.totalTimeInForeground }
            ?.take(limit)
            ?.map { stat ->
                val appName = getAppName(stat.packageName)
                Pair(appName, stat.totalTimeInForeground)
            }
            ?: emptyList()
    }

    private fun getAppName(packageName: String): String {
        return try {
            val pm = context.packageManager
            val appInfo = pm.getApplicationInfo(packageName, 0)
            pm.getApplicationLabel(appInfo).toString()
        } catch (e: PackageManager.NameNotFoundException) {
            packageName
        }
    }
}
