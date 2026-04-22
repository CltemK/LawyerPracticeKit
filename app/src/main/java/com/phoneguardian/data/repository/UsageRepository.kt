package com.phoneguardian.data.repository

import android.app.usage.UsageStats
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.pm.ApplicationInfo
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
        val startOfDay = TimeUtils.getStartOfDay()
        val endOfDay = System.currentTimeMillis()
        return getAppsForPeriod(startOfDay, endOfDay, limit)
    }

    fun getAppsForPeriod(startTime: Long, endTime: Long, limit: Int = 10): List<Pair<String, Long>> {
        val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager

        val usageStats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startTime,
            endTime
        )

        return usageStats
            ?.filter { it.totalTimeInForeground > 30 * 1000 } // 过滤使用少于30秒的
            ?.filter { !isSystemApp(it.packageName) } // 过滤系统应用
            ?.sortedByDescending { it.totalTimeInForeground }
            ?.take(limit)
            ?.map { stat ->
                val appName = getAppName(stat.packageName)
                Pair(appName, stat.totalTimeInForeground)
            }
            ?: emptyList()
    }

    private fun isSystemApp(packageName: String): Boolean {
        return try {
            val appInfo = context.packageManager.getApplicationInfo(packageName, 0)
            (appInfo.flags and ApplicationInfo.FLAG_SYSTEM) != 0 &&
                    context.packageManager.getApplicationLabel(appInfo).toString() == packageName
        } catch (e: PackageManager.NameNotFoundException) {
            true // 找不到的应用视为系统应用
        }
    }

    private fun getAppName(packageName: String): String {
        return try {
            val appInfo = context.packageManager.getApplicationInfo(packageName, 0)
            val label = context.packageManager.getApplicationLabel(appInfo).toString()
            // 如果返回的是包名而不是真正的名称，尝试提取最后一段
            if (label == packageName) {
                packageName.substringAfterLast('.')
            } else {
                label
            }
        } catch (e: PackageManager.NameNotFoundException) {
            packageName.substringAfterLast('.')
        }
    }
}
