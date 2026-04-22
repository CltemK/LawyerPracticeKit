package com.phoneguardian.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "screen_sessions")
data class ScreenSession(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val startTime: Long,
    val endTime: Long,
    val durationMs: Long,
    val date: String // "yyyy-MM-dd"
)
