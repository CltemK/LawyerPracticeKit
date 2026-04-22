package com.phoneguardian.data.local.dao

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.google.common.truth.Truth.assertThat
import com.phoneguardian.data.local.AppDatabase
import com.phoneguardian.data.local.entity.DailySummary
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DailySummaryDaoTest {

    private lateinit var database: AppDatabase
    private lateinit var dao: DailySummaryDao

    @Before
    fun setup() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).allowMainThreadQueries().build()
        dao = database.dailySummaryDao()
    }

    @After
    fun teardown() {
        database.close()
    }

    @Test
    fun insert_andGetSummaryByDate() = runTest {
        val summary = DailySummary(
            date = "2024-03-15",
            totalScreenMs = 3600000L,
            sleepScreenMs = 600000L,
            batteryDrain = 25,
            topApps = """[{"pkg":"微信","ms":1800000}]"""
        )
        dao.insert(summary)

        val result = dao.getSummaryByDate("2024-03-15").first()
        assertThat(result).isNotNull()
        assertThat(result!!.totalScreenMs).isEqualTo(3600000L)
        assertThat(result.batteryDrain).isEqualTo(25)
    }

    @Test
    fun getSummaryByDate_noMatch_returnsNull() = runTest {
        val result = dao.getSummaryByDate("2024-03-15").first()
        assertThat(result).isNull()
    }

    @Test
    fun insert_onConflictReplace() = runTest {
        dao.insert(DailySummary(date = "2024-03-15", totalScreenMs = 1000L, sleepScreenMs = 100L, batteryDrain = 5, topApps = ""))
        dao.insert(DailySummary(date = "2024-03-15", totalScreenMs = 2000L, sleepScreenMs = 200L, batteryDrain = 10, topApps = ""))

        val result = dao.getSummaryByDate("2024-03-15").first()
        assertThat(result!!.totalScreenMs).isEqualTo(2000L)
        assertThat(result.batteryDrain).isEqualTo(10)
    }

    @Test
    fun getSummariesBetween_returnsCorrectRange() = runTest {
        dao.insert(DailySummary(date = "2024-03-14", totalScreenMs = 1000L, sleepScreenMs = 100L, batteryDrain = 5, topApps = ""))
        dao.insert(DailySummary(date = "2024-03-15", totalScreenMs = 2000L, sleepScreenMs = 200L, batteryDrain = 10, topApps = ""))
        dao.insert(DailySummary(date = "2024-03-16", totalScreenMs = 3000L, sleepScreenMs = 300L, batteryDrain = 15, topApps = ""))

        val summaries = dao.getSummariesBetween("2024-03-15", "2024-03-16").first()
        assertThat(summaries).hasSize(2)
    }

    @Test
    fun getRecentSummaries_returnsLimitedResults() = runTest {
        for (i in 10..15) {
            dao.insert(DailySummary(date = "2024-03-$i", totalScreenMs = 1000L, sleepScreenMs = 100L, batteryDrain = 5, topApps = ""))
        }

        val summaries = dao.getRecentSummaries(3).first()
        assertThat(summaries).hasSize(3)
    }

    @Test
    fun deleteOldData_removesOldSummaries() = runTest {
        dao.insert(DailySummary(date = "2024-03-10", totalScreenMs = 1000L, sleepScreenMs = 100L, batteryDrain = 5, topApps = ""))
        dao.insert(DailySummary(date = "2024-03-15", totalScreenMs = 2000L, sleepScreenMs = 200L, batteryDrain = 10, topApps = ""))

        dao.deleteOldData("2024-03-13")

        assertThat(dao.getSummaryByDate("2024-03-10").first()).isNull()
        assertThat(dao.getSummaryByDate("2024-03-15").first()).isNotNull()
    }
}
