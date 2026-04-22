package com.phoneguardian.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.phoneguardian.R
import com.phoneguardian.data.repository.BatteryRepository
import com.phoneguardian.data.repository.ScreenRepository
import com.phoneguardian.ui.MainActivity
import com.phoneguardian.util.TimeUtils
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class MonitorService : Service() {

    companion object {
        private const val TAG = "MonitorService"
        private const val CHANNEL_ID = "monitor_channel"
        private const val NOTIFICATION_ID = 1

        const val ACTION_SCREEN_ON = "com.phoneguardian.ACTION_SCREEN_ON"
        const val ACTION_SCREEN_OFF = "com.phoneguardian.ACTION_SCREEN_OFF"
        const val ACTION_BATTERY_UPDATE = "com.phoneguardian.ACTION_BATTERY_UPDATE"
    }

    private val screenRepository by lazy { ScreenRepository() }
    private val batteryRepository by lazy { BatteryRepository() }

    private var screenOnTime: Long = 0L
    private var currentSessionStart: Long = 0L

    private val screenReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                Intent.ACTION_SCREEN_ON -> {
                    screenOnTime = System.currentTimeMillis()
                    currentSessionStart = screenOnTime
                    Log.d(TAG, "Screen ON at $screenOnTime")
                }
                Intent.ACTION_SCREEN_OFF -> {
                    val screenOffTime = System.currentTimeMillis()
                    val duration = screenOffTime - screenOnTime

                    if (duration > 500) {
                        Log.d(TAG, "Screen OFF after ${duration}ms")
                        CoroutineScope(Dispatchers.IO).launch {
                            screenRepository.saveSession(screenOnTime, screenOffTime)
                            batteryRepository.updateActiveCycleScreenTime(duration)
                        }
                    }
                    currentSessionStart = 0L
                }
            }
        }
    }

    private val batteryReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (intent.action == Intent.ACTION_BATTERY_CHANGED) {
                val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
                val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
                val percentage = if (level >= 0 && scale > 0) (level * 100) / scale else 0

                val status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
                val isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                        status == BatteryManager.BATTERY_STATUS_FULL

                val plugged = intent.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0)
                val chargeType = when (plugged) {
                    BatteryManager.BATTERY_PLUGGED_AC -> 2
                    BatteryManager.BATTERY_PLUGGED_USB -> 1
                    BatteryManager.BATTERY_PLUGGED_WIRELESS -> 3
                    else -> 0
                }

                Log.d(TAG, "Battery: $percentage%, charging=$isCharging")
                CoroutineScope(Dispatchers.IO).launch {
                    batteryRepository.saveBatteryEvent(percentage, isCharging, chargeType)
                }
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        registerReceivers()
        Log.d(TAG, "MonitorService created")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, buildNotification())
        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            unregisterReceiver(screenReceiver)
            unregisterReceiver(batteryReceiver)
        } catch (e: Exception) {
            Log.w(TAG, "Error unregistering receivers", e)
        }
        Log.d(TAG, "MonitorService destroyed")
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun registerReceivers() {
        val screenFilter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_ON)
            addAction(Intent.ACTION_SCREEN_OFF)
        }
        registerReceiver(screenReceiver, screenFilter)

        val batteryFilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        registerReceiver(batteryReceiver, batteryFilter)

        // Immediately get current battery state
        val batteryIntent = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        batteryIntent?.let {
            val level = it.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
            val scale = it.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
            val percentage = if (level >= 0 && scale > 0) (level * 100) / scale else 0
            val status = it.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
            val isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                    status == BatteryManager.BATTERY_STATUS_FULL

            CoroutineScope(Dispatchers.IO).launch {
                batteryRepository.saveBatteryEvent(percentage, isCharging, 0)
            }
        }
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "手机守护监控",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "保持屏幕和电量监控运行"
            setShowBadge(false)
        }
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }

    private fun buildNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("手机守护运行中")
            .setContentText("正在监控亮屏时长和电池状态")
            .setSmallIcon(R.drawable.ic_dashboard)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }
}
