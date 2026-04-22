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

class PowerReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "PowerReceiver"
    }

    private val batteryRepository = BatteryRepository()

    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            Intent.ACTION_POWER_CONNECTED -> {
                Log.d(TAG, "Power connected")
                CoroutineScope(Dispatchers.IO).launch {
                    val level = getCurrentBatteryLevel(context)
                    batteryRepository.startChargeCycle(level)
                }
            }
            Intent.ACTION_POWER_DISCONNECTED -> {
                Log.d(TAG, "Power disconnected")
                CoroutineScope(Dispatchers.IO).launch {
                    val level = getCurrentBatteryLevel(context)
                    batteryRepository.endChargeCycle(level, 0)
                }
            }
        }
    }

    private fun getCurrentBatteryLevel(context: Context): Int {
        val batteryManager = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        return batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    }
}
