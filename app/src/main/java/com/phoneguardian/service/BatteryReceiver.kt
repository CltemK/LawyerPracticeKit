package com.phoneguardian.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.BatteryManager
import android.util.Log
import com.phoneguardian.data.repository.BatteryRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class BatteryReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "BatteryReceiver"
    }

    private val batteryRepository = BatteryRepository()

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

            Log.d(TAG, "Battery changed: $percentage%, charging=$isCharging")

            CoroutineScope(Dispatchers.IO).launch {
                batteryRepository.saveBatteryEvent(percentage, isCharging, chargeType)
            }
        }
    }
}
