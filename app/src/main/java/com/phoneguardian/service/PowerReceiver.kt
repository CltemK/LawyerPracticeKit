package com.phoneguardian.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * Power events are now handled by MonitorService.
 */
class PowerReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        Log.d("PowerReceiver", "Received: ${intent.action} — handled by MonitorService")
    }
}
