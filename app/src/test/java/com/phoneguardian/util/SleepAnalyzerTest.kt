package com.phoneguardian.util

import com.google.common.truth.Truth.assertThat
import com.phoneguardian.data.local.entity.ScreenSession
import org.junit.Test
import java.util.Calendar

class SleepAnalyzerTest {

    private val analyzer = SleepAnalyzer(
        sleepStartHour = 22,
        sleepStartMinute = 0,
        sleepEndHour = 7,
        sleepEndMinute = 0
    )

    private fun makeTimestamp(year: Int, month: Int, day: Int, hour: Int, minute: Int): Long {
        val calendar = Calendar.getInstance()
        calendar.set(year, month, day, hour, minute, 0)
        calendar.set(Calendar.MILLISECOND, 0)
        return calendar.timeInMillis
    }

    // --- isInSleepTime tests ---

    @Test
    fun isInSleepTime_atMidnight_returnsTrue() {
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 0, 0)
        assertThat(analyzer.isInSleepTime(ts)).isTrue()
    }

    @Test
    fun isInSleepTime_at3am_returnTrue() {
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 3, 0)
        assertThat(analyzer.isInSleepTime(ts)).isTrue()
    }

    @Test
    fun isInSleepTime_at6_59am_returnTrue() {
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 6, 59)
        assertThat(analyzer.isInSleepTime(ts)).isTrue()
    }

    @Test
    fun isInSleepTime_at7am_returnFalse() {
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 7, 0)
        assertThat(analyzer.isInSleepTime(ts)).isFalse()
    }

    @Test
    fun isInSleepTime_at12pm_returnFalse() {
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 12, 0)
        assertThat(analyzer.isInSleepTime(ts)).isFalse()
    }

    @Test
    fun isInSleepTime_at10pm_returnTrue() {
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 22, 0)
        assertThat(analyzer.isInSleepTime(ts)).isTrue()
    }

    @Test
    fun isInSleepTime_at11pm_returnTrue() {
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 23, 0)
        assertThat(analyzer.isInSleepTime(ts)).isTrue()
    }

    @Test
    fun isInSleepTime_at9_59pm_returnFalse() {
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 21, 59)
        assertThat(analyzer.isInSleepTime(ts)).isFalse()
    }

    // --- Same-day sleep time range ---

    @Test
    fun sameDaySleepRange_at2am_returnTrue() {
        val sameDayAnalyzer = SleepAnalyzer(
            sleepStartHour = 1,
            sleepStartMinute = 0,
            sleepEndHour = 5,
            sleepEndMinute = 0
        )
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 2, 0)
        assertThat(sameDayAnalyzer.isInSleepTime(ts)).isTrue()
    }

    @Test
    fun sameDaySleepRange_at6am_returnFalse() {
        val sameDayAnalyzer = SleepAnalyzer(
            sleepStartHour = 1,
            sleepStartMinute = 0,
            sleepEndHour = 5,
            sleepEndMinute = 0
        )
        val ts = makeTimestamp(2024, Calendar.MARCH, 15, 6, 0)
        assertThat(sameDayAnalyzer.isInSleepTime(ts)).isFalse()
    }

    // --- getSleepScreenDuration tests ---

    @Test
    fun getSleepScreenDuration_fullyInSleepTime() {
        // Session 23:00 - 23:30, fully within sleep time
        val start = makeTimestamp(2024, Calendar.MARCH, 15, 23, 0)
        val end = makeTimestamp(2024, Calendar.MARCH, 15, 23, 30)
        val session = ScreenSession(
            startTime = start,
            endTime = end,
            durationMs = end - start,
            date = "2024-03-15"
        )
        val result = analyzer.getSleepScreenDuration(listOf(session))
        assertThat(result).isEqualTo(end - start)
    }

    @Test
    fun getSleepScreenDuration_fullyOutsideSleepTime() {
        // Session 12:00 - 12:30, outside sleep time
        val start = makeTimestamp(2024, Calendar.MARCH, 15, 12, 0)
        val end = makeTimestamp(2024, Calendar.MARCH, 15, 12, 30)
        val session = ScreenSession(
            startTime = start,
            endTime = end,
            durationMs = end - start,
            date = "2024-03-15"
        )
        val result = analyzer.getSleepScreenDuration(listOf(session))
        assertThat(result).isEqualTo(0)
    }

    @Test
    fun getSleepScreenDuration_emptyList_returnsZero() {
        val result = analyzer.getSleepScreenDuration(emptyList())
        assertThat(result).isEqualTo(0)
    }

    @Test
    fun getSleepScreenDuration_multipleSessions_sumsDurations() {
        // Session 1: 23:00 - 23:10 (fully in sleep time = 10 min)
        val s1 = makeTimestamp(2024, Calendar.MARCH, 15, 23, 0)
        val e1 = makeTimestamp(2024, Calendar.MARCH, 15, 23, 10)
        val session1 = ScreenSession(startTime = s1, endTime = e1, durationMs = e1 - s1, date = "2024-03-15")

        // Session 2: 3:00 - 3:20 (fully in sleep time = 20 min)
        val s2 = makeTimestamp(2024, Calendar.MARCH, 16, 3, 0)
        val e2 = makeTimestamp(2024, Calendar.MARCH, 16, 3, 20)
        val session2 = ScreenSession(startTime = s2, endTime = e2, durationMs = e2 - s2, date = "2024-03-16")

        val result = analyzer.getSleepScreenDuration(listOf(session1, session2))
        assertThat(result).isEqualTo((e1 - s1) + (e2 - s2))
    }

    // --- getSleepPeriodForDate tests ---

    @Test
    fun getSleepPeriodForDate_startIsBeforeEnd() {
        val (sleepStart, sleepEnd) = analyzer.getSleepPeriodForDate("2024-03-16")
        assertThat(sleepStart).isLessThan(sleepEnd)
    }

    @Test
    fun getSleepPeriodForDate_sleepStartIsPreviousNight() {
        val (sleepStart, sleepEnd) = analyzer.getSleepPeriodForDate("2024-03-16")

        val startCal = Calendar.getInstance()
        startCal.timeInMillis = sleepStart
        assertThat(startCal.get(Calendar.DAY_OF_MONTH)).isEqualTo(15) // Previous day
        assertThat(startCal.get(Calendar.HOUR_OF_DAY)).isEqualTo(22)

        val endCal = Calendar.getInstance()
        endCal.timeInMillis = sleepEnd
        assertThat(endCal.get(Calendar.DAY_OF_MONTH)).isEqualTo(16) // Current day
        assertThat(endCal.get(Calendar.HOUR_OF_DAY)).isEqualTo(7)
    }
}
