package com.phoneguardian.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "daily_summary")
data class DailySummary(
    @PrimaryKey
    val date: String, // "yyyy-MM-dd"
    val totalScreenMs: Long,
    val sleepScreenMs: Long, // 睡眠时段亮屏时长
    val batteryDrain: Int, // 当日电量消耗
    val topApps: String // JSON: [{"pkg":"微信","ms":xxx},...]
)
