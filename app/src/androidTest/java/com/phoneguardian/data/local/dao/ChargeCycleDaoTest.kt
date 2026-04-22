package com.phoneguardian.data.local.dao

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.google.common.truth.Truth.assertThat
import com.phoneguardian.data.local.AppDatabase
import com.phoneguardian.data.local.entity.ChargeCycle
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ChargeCycleDaoTest {

    private lateinit var database: AppDatabase
    private lateinit var dao: ChargeCycleDao

    @Before
    fun setup() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).allowMainThreadQueries().build()
        dao = database.chargeCycleDao()
    }

    @After
    fun teardown() {
        database.close()
    }

    @Test
    fun insert_andGetActiveCycle() = runTest {
        dao.insert(ChargeCycle(
            startTime = 1000L, endTime = null, startLevel = 20,
            endLevel = null, screenMsDuringCharge = 0, date = "2024-03-15"
        ))

        val active = dao.getActiveCycle()
        assertThat(active).isNotNull()
        assertThat(active!!.startLevel).isEqualTo(20)
        assertThat(active.endTime).isNull()
    }

    @Test
    fun getActiveCycle_noActiveCycle_returnsNull() = runTest {
        dao.insert(ChargeCycle(
            startTime = 1000L, endTime = 5000L, startLevel = 20,
            endLevel = 80, screenMsDuringCharge = 100L, date = "2024-03-15"
        ))

        val active = dao.getActiveCycle()
        assertThat(active).isNull()
    }

    @Test
    fun update_completesChargeCycle() = runTest {
        val id = dao.insert(ChargeCycle(
            startTime = 1000L, endTime = null, startLevel = 20,
            endLevel = null, screenMsDuringCharge = 0, date = "2024-03-15"
        ))

        val cycle = dao.getActiveCycle()!!
        val updated = cycle.copy(endTime = 5000L, endLevel = 80, screenMsDuringCharge = 500L)
        dao.update(updated)

        assertThat(dao.getActiveCycle()).isNull()
        val recent = dao.getRecentCycles(1).first()
        assertThat(recent[0].endLevel).isEqualTo(80)
    }

    @Test
    fun getCyclesByDate_returnsCorrectCycles() = runTest {
        dao.insert(ChargeCycle(startTime = 1L, endTime = 2L, startLevel = 20, endLevel = 80, screenMsDuringCharge = 0, date = "2024-03-15"))
        dao.insert(ChargeCycle(startTime = 3L, endTime = 4L, startLevel = 30, endLevel = 90, screenMsDuringCharge = 0, date = "2024-03-16"))

        val cycles = dao.getCyclesByDate("2024-03-15").first()
        assertThat(cycles).hasSize(1)
        assertThat(cycles[0].startLevel).isEqualTo(20)
    }

    @Test
    fun getRecentCycles_returnsLimitedResults() = runTest {
        dao.insert(ChargeCycle(startTime = 1L, endTime = 2L, startLevel = 20, endLevel = 80, screenMsDuringCharge = 0, date = "2024-03-15"))
        dao.insert(ChargeCycle(startTime = 3L, endTime = 4L, startLevel = 30, endLevel = 90, screenMsDuringCharge = 0, date = "2024-03-16"))
        dao.insert(ChargeCycle(startTime = 5L, endTime = 6L, startLevel = 40, endLevel = 100, screenMsDuringCharge = 0, date = "2024-03-17"))

        val cycles = dao.getRecentCycles(2).first()
        assertThat(cycles).hasSize(2)
    }

    @Test
    fun deleteOldData_removesOldCycles() = runTest {
        dao.insert(ChargeCycle(startTime = 1000L, endTime = 2000L, startLevel = 20, endLevel = 80, screenMsDuringCharge = 0, date = "2024-03-15"))
        dao.insert(ChargeCycle(startTime = 3000L, endTime = 4000L, startLevel = 30, endLevel = 90, screenMsDuringCharge = 0, date = "2024-03-16"))

        dao.deleteOldData(2500L)

        val cycles = dao.getRecentCycles(10).first()
        assertThat(cycles).hasSize(1)
        assertThat(cycles[0].startLevel).isEqualTo(30)
    }
}
