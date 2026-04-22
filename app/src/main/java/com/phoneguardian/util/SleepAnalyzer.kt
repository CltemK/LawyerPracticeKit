package com.phoneguardian.util

import com.phoneguardian.data.local.entity.ScreenSession
import java.util.Calendar

class SleepAnalyzer(
    private val sleepStartHour: Int = 22,
    private val sleepStartMinute: Int = 0,
    private val sleepEndHour: Int = 7,
    private val sleepEndMinute: Int = 0
) {

    fun isInSleepTime(timestamp: Long): Boolean {
        val calendar = Calendar.getInstance()
        calendar.timeInMillis = timestamp
        val hour = calendar.get(Calendar.HOUR_OF_DAY)
        val minute = calendar.get(Calendar.MINUTE)

        return when {
            sleepStartHour > sleepEndHour -> {
                // 跨越午夜，如 22:00 - 07:00
                if (hour >= sleepStartHour) {
                    hour > sleepStartHour || minute >= sleepStartMinute
                } else {
                    hour < sleepEndHour || (hour == sleepEndHour && minute < sleepEndMinute)
                }
            }
            else -> {
                // 同一天，如 02:00 - 05:00
                val currentMinutes = hour * 60 + minute
                val startMinutes = sleepStartHour * 60 + sleepStartMinute
                val endMinutes = sleepEndHour * 60 + sleepEndMinute
                currentMinutes in startMinutes until endMinutes
            }
        }
    }

    fun getSleepScreenDuration(sessions: List<ScreenSession>): Long {
        return sessions
            .filter { session ->
                isInSleepTime(session.startTime) || isInSleepTime(session.endTime)
            }
            .sumOf { session ->
                val effectiveStart = if (isInSleepTime(session.startTime)) {
                    session.startTime
                } else {
                    getSleepStartOfSession(session)
                }

                val effectiveEnd = if (isInSleepTime(session.endTime)) {
                    session.endTime
                } else {
                    getSleepEndOfSession(session)
                }

                if (effectiveEnd > effectiveStart) effectiveEnd - effectiveStart else 0
            }
    }

    private fun getSleepStartOfSession(session: ScreenSession): Long {
        val calendar = Calendar.getInstance()
        calendar.timeInMillis = session.startTime

        if (calendar.get(Calendar.HOUR_OF_DAY) < sleepEndHour) {
            // 凌晨的使用，算入睡眠时段
            return session.startTime
        }

        // 找到下一个 sleepStart
        calendar.set(Calendar.HOUR_OF_DAY, sleepStartHour)
        calendar.set(Calendar.MINUTE, sleepStartMinute)
        calendar.set(Calendar.SECOND, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        if (calendar.timeInMillis <= session.startTime) {
            calendar.add(Calendar.DAY_OF_YEAR, 1)
        }
        return calendar.timeInMillis
    }

    private fun getSleepEndOfSession(session: ScreenSession): Long {
        val calendar = Calendar.getInstance()
        calendar.timeInMillis = session.endTime

        if (calendar.get(Calendar.HOUR_OF_DAY) >= sleepStartHour) {
            // 晚上的使用，算入睡眠时段
            return session.endTime
        }

        // 找到上一个 sleepEnd
        calendar.set(Calendar.HOUR_OF_DAY, sleepEndHour)
        calendar.set(Calendar.MINUTE, sleepEndMinute)
        calendar.set(Calendar.SECOND, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        if (calendar.timeInMillis > session.endTime) {
            calendar.add(Calendar.DAY_OF_YEAR, -1)
        }
        return calendar.timeInMillis
    }

    fun getSleepPeriodForDate(date: String): Pair<Long, Long> {
        val dateFormat = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.getDefault())
        val calendar = java.util.Calendar.getInstance()
        calendar.time = dateFormat.parse(date) ?: java.util.Date()

        // 睡眠开始是前一天的 sleepStartHour
        calendar.add(Calendar.DAY_OF_YEAR, -1)
        calendar.set(Calendar.HOUR_OF_DAY, sleepStartHour)
        calendar.set(Calendar.MINUTE, sleepStartMinute)
        calendar.set(Calendar.SECOND, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        val sleepStart = calendar.timeInMillis

        // 睡眠结束是当天的 sleepEndHour
        calendar.add(Calendar.DAY_OF_YEAR, 1)
        calendar.set(Calendar.HOUR_OF_DAY, sleepEndHour)
        calendar.set(Calendar.MINUTE, sleepEndMinute)
        val sleepEnd = calendar.timeInMillis

        return Pair(sleepStart, sleepEnd)
    }
}
