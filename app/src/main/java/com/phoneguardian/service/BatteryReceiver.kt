package com.phoneguardian.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * Battery events are now handled by MonitorService via dynamic registration.
 * This static receiver is kept as fallback only.
 */
class BatteryReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        Log.d("BatteryReceiver", "Received: ${intent.action} — handled by MonitorService")
    }
}
