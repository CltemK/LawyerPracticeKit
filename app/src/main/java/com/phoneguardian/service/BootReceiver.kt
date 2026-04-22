package com.phoneguardian.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

class BootReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "BootReceiver"
        private const val DAILY_SUMMARY_WORK = "daily_summary_work"
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            Log.d(TAG, "Boot completed, starting monitor service")

            // 启动监控前台服务
            val serviceIntent = Intent(context, MonitorService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(serviceIntent)
            } else {
                context.startService(serviceIntent)
            }

            // 重新调度每日汇总任务
            scheduleDailySummary(context)
        }
    }

    private fun scheduleDailySummary(context: Context) {
        val workRequest = PeriodicWorkRequestBuilder<DailySummaryWorker>(
            1, TimeUnit.DAYS
        )
            .setInitialDelay(calculateInitialDelay(), TimeUnit.MILLISECONDS)
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            DAILY_SUMMARY_WORK,
            ExistingPeriodicWorkPolicy.KEEP,
            workRequest
        )
    }

    private fun calculateInitialDelay(): Long {
        val now = java.util.Calendar.getInstance()
        val target = java.util.Calendar.getInstance().apply {
            set(java.util.Calendar.HOUR_OF_DAY, 0)
            set(java.util.Calendar.MINUTE, 5)
            set(java.util.Calendar.SECOND, 0)
            set(java.util.Calendar.MILLISECOND, 0)
        }

        if (target.before(now)) {
            target.add(java.util.Calendar.DAY_OF_YEAR, 1)
        }

        return target.timeInMillis - now.timeInMillis
    }
}
