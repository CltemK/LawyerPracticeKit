package com.phoneguardian.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.phoneguardian.data.repository.ScreenRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class ScreenReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "ScreenReceiver"
        private var screenOnTime: Long = 0
    }

    private val screenRepository = ScreenRepository()
    private val batteryRepository = com.phoneguardian.data.repository.BatteryRepository()

    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            Intent.ACTION_SCREEN_ON -> {
                screenOnTime = System.currentTimeMillis()
                Log.d(TAG, "Screen ON at $screenOnTime")
            }
            Intent.ACTION_SCREEN_OFF -> {
                val screenOffTime = System.currentTimeMillis()
                val duration = screenOffTime - screenOnTime

                if (duration > 1000) { // 过滤掉短时间的亮屏（如按键唤醒）
                    Log.d(TAG, "Screen OFF after ${duration}ms")
                    CoroutineScope(Dispatchers.IO).launch {
                        screenRepository.saveSession(screenOnTime, screenOffTime)
                        batteryRepository.updateActiveCycleScreenTime(duration)
                    }
                }
            }
        }
    }
}
