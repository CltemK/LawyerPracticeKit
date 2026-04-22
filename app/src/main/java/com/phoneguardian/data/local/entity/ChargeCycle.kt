package com.phoneguardian.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "charge_cycles")
data class ChargeCycle(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val startTime: Long, // 开始充电时间
    val endTime: Long?, // 结束充电时间，null表示正在充电
    val startLevel: Int, // 开始充电时电量
    val endLevel: Int?, // 结束充电时电量，null表示正在充电
    val screenMsDuringCharge: Long, // 充电期间的亮屏时长
    val date: String // "yyyy-MM-dd" 充电周期结束的日期
)
