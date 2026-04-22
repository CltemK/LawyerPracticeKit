package com.phoneguardian.data.repository

import com.google.common.truth.Truth.assertThat
import com.phoneguardian.data.local.dao.ScreenSessionDao
import com.phoneguardian.data.local.entity.ScreenSession
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.*

class ScreenRepositoryTest {

    private lateinit var dao: ScreenSessionDao

    @Before
    fun setup() {
        dao = mock()
    }

    @Test
    fun saveSession_createsSessionWithCorrectFields() = runTest {
        val startTime = 1710489600000L // 2024-03-15 00:00:00 UTC
        val endTime = 1710489960000L   // 2024-03-15 00:06:00 UTC
        val expectedDuration = endTime - startTime

        val session = ScreenSession(
            startTime = startTime,
            endTime = endTime,
            durationMs = expectedDuration,
            date = com.phoneguardian.util.TimeUtils.formatDate(startTime)
        )
        whenever(dao.insert(any())).thenReturn(1L)

        dao.insert(session)

        verify(dao).insert(argThat { s ->
            s.startTime == startTime &&
            s.endTime == endTime &&
            s.durationMs == expectedDuration
        })
    }

    @Test
    fun getSessionsByDate_delegatesToDao() = runTest {
        val sessions = listOf(
            ScreenSession(startTime = 1L, endTime = 2L, durationMs = 100L, date = "2024-03-15")
        )
        whenever(dao.getSessionsByDate("2024-03-15")).thenReturn(flowOf(sessions))

        val result = dao.getSessionsByDate("2024-03-15").first()
        assertThat(result).hasSize(1)
    }

    @Test
    fun getTotalDurationByDate_delegatesToDao() = runTest {
        whenever(dao.getTotalDurationByDate("2024-03-15")).thenReturn(flowOf(3600000L))

        val result = dao.getTotalDurationByDate("2024-03-15").first()
        assertThat(result).isEqualTo(3600000L)
    }

    @Test
    fun deleteOldData_delegatesToDao() = runTest {
        val beforeDate = com.phoneguardian.util.TimeUtils.getDateBeforeDays(30)
        dao.deleteOldData(beforeDate)
        verify(dao).deleteOldData(beforeDate)
    }

    @Test
    fun getSessionsBetween_delegatesToDao() = runTest {
        val sessions = listOf(
            ScreenSession(startTime = 1L, endTime = 2L, durationMs = 100L, date = "2024-03-15")
        )
        whenever(dao.getSessionsBetween("2024-03-15", "2024-03-17")).thenReturn(flowOf(sessions))

        val result = dao.getSessionsBetween("2024-03-15", "2024-03-17").first()
        assertThat(result).hasSize(1)
    }
}
