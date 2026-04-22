package com.phoneguardian.service

import android.content.Context
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.phoneguardian.PhoneGuardianApp
import com.phoneguardian.data.datastore.SettingsDataStore
import com.phoneguardian.data.local.entity.DailySummary
import com.phoneguardian.data.repository.ScreenRepository
import com.phoneguardian.data.repository.UsageRepository
import com.phoneguardian.util.SleepAnalyzer
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.flow.first
import org.json.JSONArray

class DailySummaryWorker(
    context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    companion object {
        private const val TAG = "DailySummaryWorker"
    }

    private val screenRepository = ScreenRepository()
    private val usageRepository = UsageRepository()
    private val settingsDataStore = SettingsDataStore(context)

    override suspend fun doWork(): Result {
        return try {
            Log.d(TAG, "Starting daily summary work")

            val yesterday = TimeUtils.getYesterdayString()
            val sleepStartTime = settingsDataStore.sleepStartTime.first()
            val sleepEndTime = settingsDataStore.sleepEndTime.first()

            val (startHour, startMinute) = TimeUtils.parseTime(sleepStartTime)
            val (endHour, endMinute) = TimeUtils.parseTime(sleepEndTime)

            val sleepAnalyzer = SleepAnalyzer(startHour, startMinute, endHour, endMinute)

            // 获取昨天的亮屏会话
            val sessions = screenRepository.getSessionsByDate(yesterday).first()

            // 计算总亮屏时长
            val totalScreenMs = sessions.sumOf { it.durationMs }

            // 计算睡眠时段亮屏时长
            val sleepScreenMs = sleepAnalyzer.getSleepScreenDuration(sessions)

            // 获取 TOP 3 应用
            val topApps = usageRepository.getTopAppsToday(3)
            val topAppsJson = JSONArray().apply {
                topApps.forEach { (name, ms) ->
                    put(org.json.JSONObject().apply {
                        put("name", name)
                        put("ms", ms)
                    })
                }
            }.toString()

            // 创建每日汇总
            val summary = DailySummary(
                date = yesterday,
                totalScreenMs = totalScreenMs,
                sleepScreenMs = sleepScreenMs,
                batteryDrain = 0, // 将在 BatteryReceiver 中更新
                topApps = topAppsJson
            )

            usageRepository.saveDailySummary(summary)

            Log.d(TAG, "Daily summary created for $yesterday: total=${totalScreenMs}ms, sleep=${sleepScreenMs}ms")

            // 清理旧数据
            val retentionDays = settingsDataStore.dataRetentionDays.first()
            screenRepository.deleteOldData(retentionDays)
            usageRepository.deleteOldSummaries(retentionDays)

            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "Error in daily summary work", e)
            Result.retry()
        }
    }
}
