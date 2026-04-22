package com.phoneguardian.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "battery_events")
data class BatteryEvent(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val timestamp: Long,
    val level: Int,
    val isCharging: Boolean,
    val chargeType: Int = 0 // 0=none, 1=usb, 2=ac, 3=wireless
)
