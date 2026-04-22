package com.phoneguardian

import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.work.Configuration
import androidx.work.WorkManager
import com.phoneguardian.data.local.AppDatabase
import com.phoneguardian.service.MonitorService

class PhoneGuardianApp : android.app.Application(), Configuration.Provider {

    lateinit var database: AppDatabase
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        database = AppDatabase.getInstance(this)

        // 启动监控前台服务
        startMonitorService()
    }

    private fun startMonitorService() {
        val intent = Intent(this, MonitorService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
        Log.d("PhoneGuardianApp", "MonitorService started")
    }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setMinimumLoggingLevel(android.util.Log.INFO)
            .build()

    companion object {
        lateinit var instance: PhoneGuardianApp
            private set
    }
}
