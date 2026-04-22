package com.phoneguardian.util

import com.google.common.truth.Truth.assertThat
import org.junit.Test
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

class TimeUtilsTest {

    private val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())

    @Test
    fun formatDate_returnsCorrectFormat() {
        val calendar = Calendar.getInstance()
        calendar.set(2024, Calendar.MARCH, 15, 10, 30, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        val result = TimeUtils.formatDate(calendar.timeInMillis)
        assertThat(result).isEqualTo("2024-03-15")
    }

    @Test
    fun formatTime_returnsCorrectFormat() {
        val calendar = Calendar.getInstance()
        calendar.set(2024, Calendar.MARCH, 15, 14, 5, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        val result = TimeUtils.formatTime(calendar.timeInMillis)
        assertThat(result).isEqualTo("14:05")
    }

    @Test
    fun formatDuration_withHoursAndMinutes() {
        val durationMs = (2L * 60 * 60 * 1000) + (30L * 60 * 1000) // 2h 30m
        val result = TimeUtils.formatDuration(durationMs)
        assertThat(result).isEqualTo("2h 30m")
    }

    @Test
    fun formatDuration_withOnlyMinutes() {
        val durationMs = 45L * 60 * 1000 // 45m
        val result = TimeUtils.formatDuration(durationMs)
        assertThat(result).isEqualTo("45m")
    }

    @Test
    fun formatDuration_withZeroMinutes() {
        val durationMs = 2L * 60 * 60 * 1000 // 2h 0m
        val result = TimeUtils.formatDuration(durationMs)
        assertThat(result).isEqualTo("2h 0m")
    }

    @Test
    fun formatDurationLong_withHours() {
        val durationMs = (2L * 3600 * 1000) + (30L * 60 * 1000) + (45L * 1000) // 2:30:45
        val result = TimeUtils.formatDurationLong(durationMs)
        assertThat(result).isEqualTo("2:30:45")
    }

    @Test
    fun formatDurationLong_withoutHours() {
        val durationMs = (5L * 60 * 1000) + (30L * 1000) // 5:30
        val result = TimeUtils.formatDurationLong(durationMs)
        assertThat(result).isEqualTo("5:30")
    }

    @Test
    fun parseTime_returnsCorrectPair() {
        val result = TimeUtils.parseTime("14:30")
        assertThat(result.first).isEqualTo(14)
        assertThat(result.second).isEqualTo(30)
    }

    @Test
    fun parseTime_midnight() {
        val result = TimeUtils.parseTime("00:00")
        assertThat(result.first).isEqualTo(0)
        assertThat(result.second).isEqualTo(0)
    }

    @Test
    fun getStartOfDay_returnsMidnight() {
        val result = TimeUtils.getStartOfDay("2024-03-15")
        val calendar = Calendar.getInstance()
        calendar.timeInMillis = result
        assertThat(calendar.get(Calendar.HOUR_OF_DAY)).isEqualTo(0)
        assertThat(calendar.get(Calendar.MINUTE)).isEqualTo(0)
        assertThat(calendar.get(Calendar.SECOND)).isEqualTo(0)
        assertThat(calendar.get(Calendar.MILLISECOND)).isEqualTo(0)
    }

    @Test
    fun getEndOfDay_returnsLastMillisecond() {
        val result = TimeUtils.getEndOfDay("2024-03-15")
        val calendar = Calendar.getInstance()
        calendar.timeInMillis = result
        assertThat(calendar.get(Calendar.HOUR_OF_DAY)).isEqualTo(23)
        assertThat(calendar.get(Calendar.MINUTE)).isEqualTo(59)
        assertThat(calendar.get(Calendar.SECOND)).isEqualTo(59)
        assertThat(calendar.get(Calendar.MILLISECOND)).isEqualTo(999)
    }

    @Test
    fun getStartOfDay_beforeEndOfDay() {
        val start = TimeUtils.getStartOfDay("2024-03-15")
        val end = TimeUtils.getEndOfDay("2024-03-15")
        assertThat(start).isLessThan(end)
    }

    @Test
    fun getDatesBetween_sameDate_returnsSingleDate() {
        val result = TimeUtils.getDatesBetween("2024-03-15", "2024-03-15")
        assertThat(result).hasSize(1)
        assertThat(result[0]).isEqualTo("2024-03-15")
    }

    @Test
    fun getDatesBetween_threeDays_returnsThreeDates() {
        val result = TimeUtils.getDatesBetween("2024-03-15", "2024-03-17")
        assertThat(result).hasSize(3)
        assertThat(result).containsExactly("2024-03-15", "2024-03-16", "2024-03-17")
    }

    @Test
    fun getDatesBetween_reversedDates_returnsEmpty() {
        val result = TimeUtils.getDatesBetween("2024-03-17", "2024-03-15")
        assertThat(result).isEmpty()
    }

    @Test
    fun getDatesBetween_crossMonth() {
        val result = TimeUtils.getDatesBetween("2024-02-28", "2024-03-01")
        assertThat(result).hasSize(3)
        assertThat(result[0]).isEqualTo("2024-02-28")
        assertThat(result[1]).isEqualTo("2024-02-29") // 2024 is leap year
        assertThat(result[2]).isEqualTo("2024-03-01")
    }

    @Test
    fun getTodayString_matchesFormatDate() {
        val today = TimeUtils.getTodayString()
        val expected = TimeUtils.formatDate(System.currentTimeMillis())
        assertThat(today).isEqualTo(expected)
    }

    @Test
    fun getYesterdayString_isOneDayBeforeToday() {
        val today = TimeUtils.getTodayString()
        val yesterday = TimeUtils.getYesterdayString()
        val todayCal = Calendar.getInstance()
        todayCal.time = dateFormat.parse(today)!!
        val yesterdayCal = Calendar.getInstance()
        yesterdayCal.time = dateFormat.parse(yesterday)!!
        val diffMs = todayCal.timeInMillis - yesterdayCal.timeInMillis
        val diffDays = diffMs / (24 * 60 * 60 * 1000)
        assertThat(diffDays).isEqualTo(1)
    }

    @Test
    fun getWeekDates_returnsSevenDates() {
        val result = TimeUtils.getWeekDates()
        assertThat(result).hasSize(7)
    }

    @Test
    fun getDateBeforeDays_returnsCorrectDate() {
        val result = TimeUtils.getDateBeforeDays(1)
        val expected = TimeUtils.getYesterdayString()
        assertThat(result).isEqualTo(expected)
    }
}
