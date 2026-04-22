package com.phoneguardian.data.local.dao

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.google.common.truth.Truth.assertThat
import com.phoneguardian.data.local.AppDatabase
import com.phoneguardian.data.local.entity.BatteryEvent
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class BatteryEventDaoTest {

    private lateinit var database: AppDatabase
    private lateinit var dao: BatteryEventDao

    @Before
    fun setup() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).allowMainThreadQueries().build()
        dao = database.batteryEventDao()
    }

    @After
    fun teardown() {
        database.close()
    }

    @Test
    fun insert_andGetLatestEvent() = runTest {
        dao.insert(BatteryEvent(timestamp = 1000L, level = 80, isCharging = true, chargeType = 2))
        dao.insert(BatteryEvent(timestamp = 2000L, level = 85, isCharging = true, chargeType = 2))

        val latest = dao.getLatestEvent().first()
        assertThat(latest).isNotNull()
        assertThat(latest!!.level).isEqualTo(85)
    }

    @Test
    fun getLatestEvent_noEvents_returnsNull() = runTest {
        val latest = dao.getLatestEvent().first()
        assertThat(latest).isNull()
    }

    @Test
    fun getEventsBetween_returnsEventsInRange() = runTest {
        dao.insert(BatteryEvent(timestamp = 1000L, level = 80, isCharging = false, chargeType = 0))
        dao.insert(BatteryEvent(timestamp = 2000L, level = 75, isCharging = false, chargeType = 0))
        dao.insert(BatteryEvent(timestamp = 3000L, level = 70, isCharging = false, chargeType = 0))

        val events = dao.getEventsBetween(1500L, 2500L).first()
        assertThat(events).hasSize(1)
        assertThat(events[0].level).isEqualTo(75)
    }

    @Test
    fun getTodayEvents_returnsEventsAfterStartOfDay() = runTest {
        dao.insert(BatteryEvent(timestamp = 500L, level = 90, isCharging = false, chargeType = 0))
        dao.insert(BatteryEvent(timestamp = 1500L, level = 85, isCharging = true, chargeType = 1))

        val events = dao.getTodayEvents(1000L).first()
        assertThat(events).hasSize(1)
        assertThat(events[0].level).isEqualTo(85)
    }

    @Test
    fun deleteOldData_removesOldEvents() = runTest {
        dao.insert(BatteryEvent(timestamp = 1000L, level = 80, isCharging = false, chargeType = 0))
        dao.insert(BatteryEvent(timestamp = 3000L, level = 70, isCharging = false, chargeType = 0))

        dao.deleteOldData(2000L)

        val events = dao.getEventsBetween(0L, 5000L).first()
        assertThat(events).hasSize(1)
        assertThat(events[0].level).isEqualTo(70)
    }
}
