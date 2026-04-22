package com.phoneguardian.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * Screen events are now handled by MonitorService.
 * This receiver is kept as fallback for direct SCREEN_ON/OFF intents.
 */
class ScreenReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        Log.d("ScreenReceiver", "Received: ${intent.action} — handled by MonitorService")
    }
}
