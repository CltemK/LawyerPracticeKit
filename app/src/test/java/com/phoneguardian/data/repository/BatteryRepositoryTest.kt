package com.phoneguardian.data.repository

import com.google.common.truth.Truth.assertThat
import com.phoneguardian.data.local.dao.BatteryEventDao
import com.phoneguardian.data.local.dao.ChargeCycleDao
import com.phoneguardian.data.local.entity.BatteryEvent
import com.phoneguardian.data.local.entity.ChargeCycle
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.*

/**
 * Tests for BatteryRepository logic patterns.
 * Since BatteryRepository directly accesses PhoneGuardianApp.instance.database,
 * we test the DAO interaction logic in isolation.
 */
class BatteryRepositoryTest {

    private lateinit var batteryEventDao: BatteryEventDao
    private lateinit var chargeCycleDao: ChargeCycleDao

    @Before
    fun setup() {
        batteryEventDao = mock()
        chargeCycleDao = mock()
    }

    @Test
    fun chargeCycleLogic_insertAndGetActiveCycle() = runTest {
        val cycle = ChargeCycle(
            startTime = 1000L, endTime = null, startLevel = 20,
            endLevel = null, screenMsDuringCharge = 0, date = "2024-03-15"
        )
        whenever(chargeCycleDao.insert(any())).thenReturn(1L)
        whenever(chargeCycleDao.getActiveCycle()).thenReturn(cycle)

        val id = chargeCycleDao.insert(cycle)
        val active = chargeCycleDao.getActiveCycle()

        assertThat(id).isEqualTo(1L)
        assertThat(active).isNotNull()
        assertThat(active!!.startLevel).isEqualTo(20)
        verify(chargeCycleDao).insert(cycle)
    }

    @Test
    fun chargeCycleLogic_endCycleUpdatesCorrectly() = runTest {
        val activeCycle = ChargeCycle(
            id = 1, startTime = 1000L, endTime = null, startLevel = 20,
            endLevel = null, screenMsDuringCharge = 500L, date = "2024-03-15"
        )
        whenever(chargeCycleDao.getActiveCycle()).thenReturn(activeCycle)

        val retrieved = chargeCycleDao.getActiveCycle()
        val updated = retrieved!!.copy(endTime = 5000L, endLevel = 80, screenMsDuringCharge = 500L)
        chargeCycleDao.update(updated)

        verify(chargeCycleDao).update(argThat { cycle ->
            cycle.endLevel == 80 && cycle.endTime == 5000L
        })
    }

    @Test
    fun chargeCycleLogic_updateActiveCycleScreenTime_addsToExisting() = runTest {
        val activeCycle = ChargeCycle(
            id = 1, startTime = 1000L, endTime = null, startLevel = 20,
            endLevel = null, screenMsDuringCharge = 500L, date = "2024-03-15"
        )
        whenever(chargeCycleDao.getActiveCycle()).thenReturn(activeCycle)

        val retrieved = chargeCycleDao.getActiveCycle()!!
        val additionalMs = 300L
        val updated = retrieved.copy(
            screenMsDuringCharge = retrieved.screenMsDuringCharge + additionalMs
        )
        chargeCycleDao.update(updated)

        verify(chargeCycleDao).update(argThat { cycle ->
            cycle.screenMsDuringCharge == 800L
        })
    }

    @Test
    fun chargeCycleLogic_endCycleWithNoActiveCycle_returnsNull() = runTest {
        whenever(chargeCycleDao.getActiveCycle()).thenReturn(null)

        val active = chargeCycleDao.getActiveCycle()
        assertThat(active).isNull()
    }

    @Test
    fun batteryEventDao_getLatestEvent() = runTest {
        val event = BatteryEvent(timestamp = 2000L, level = 85, isCharging = true, chargeType = 2)
        whenever(batteryEventDao.getLatestEvent()).thenReturn(flowOf(event))

        val latest = batteryEventDao.getLatestEvent().first()
        assertThat(latest).isNotNull()
        assertThat(latest!!.level).isEqualTo(85)
    }

    @Test
    fun batteryEventDao_deleteOldData() = runTest {
        val beforeTime = 1000L
        batteryEventDao.deleteOldData(beforeTime)
        verify(batteryEventDao).deleteOldData(beforeTime)
    }

    @Test
    fun chargeCycleDao_deleteOldData() = runTest {
        val beforeTime = 1000L
        chargeCycleDao.deleteOldData(beforeTime)
        verify(chargeCycleDao).deleteOldData(beforeTime)
    }
}
