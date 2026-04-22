package com.phoneguardian.data.local.dao

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.google.common.truth.Truth.assertThat
import com.phoneguardian.data.local.AppDatabase
import com.phoneguardian.data.local.entity.ScreenSession
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ScreenSessionDaoTest {

    private lateinit var database: AppDatabase
    private lateinit var dao: ScreenSessionDao

    @Before
    fun setup() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).allowMainThreadQueries().build()
        dao = database.screenSessionDao()
    }

    @After
    fun teardown() {
        database.close()
    }

    @Test
    fun insert_andGetSessionsByDate() = runTest {
        val session = ScreenSession(
            startTime = 1710489600000L,
            endTime = 1710489960000L,
            durationMs = 360000L,
            date = "2024-03-15"
        )
        dao.insert(session)

        val sessions = dao.getSessionsByDate("2024-03-15").first()
        assertThat(sessions).hasSize(1)
        assertThat(sessions[0].date).isEqualTo("2024-03-15")
        assertThat(sessions[0].durationMs).isEqualTo(360000L)
    }

    @Test
    fun getSessionsByDate_wrongDate_returnsEmpty() = runTest {
        val session = ScreenSession(
            startTime = 1710489600000L,
            endTime = 1710489960000L,
            durationMs = 360000L,
            date = "2024-03-15"
        )
        dao.insert(session)

        val sessions = dao.getSessionsByDate("2024-03-16").first()
        assertThat(sessions).isEmpty()
    }

    @Test
    fun getTotalDurationByDate_returnsCorrectSum() = runTest {
        dao.insert(ScreenSession(
            startTime = 1L, endTime = 2L, durationMs = 600000L, date = "2024-03-15"
        ))
        dao.insert(ScreenSession(
            startTime = 3L, endTime = 4L, durationMs = 900000L, date = "2024-03-15"
        ))

        val total = dao.getTotalDurationByDate("2024-03-15").first()
        assertThat(total).isEqualTo(1500000L)
    }

    @Test
    fun getTotalDurationByDate_noSessions_returnsNull() = runTest {
        val total = dao.getTotalDurationByDate("2024-03-15").first()
        assertThat(total).isNull()
    }

    @Test
    fun getSessionCountByDate_returnsCorrectCount() = runTest {
        dao.insert(ScreenSession(startTime = 1L, endTime = 2L, durationMs = 100L, date = "2024-03-15"))
        dao.insert(ScreenSession(startTime = 3L, endTime = 4L, durationMs = 200L, date = "2024-03-15"))
        dao.insert(ScreenSession(startTime = 5L, endTime = 6L, durationMs = 300L, date = "2024-03-16"))

        assertThat(dao.getSessionCountByDate("2024-03-15")).isEqualTo(2)
        assertThat(dao.getSessionCountByDate("2024-03-16")).isEqualTo(1)
        assertThat(dao.getSessionCountByDate("2024-03-17")).isEqualTo(0)
    }

    @Test
    fun deleteOldData_removesOldSessions() = runTest {
        dao.insert(ScreenSession(startTime = 1L, endTime = 2L, durationMs = 100L, date = "2024-03-10"))
        dao.insert(ScreenSession(startTime = 3L, endTime = 4L, durationMs = 200L, date = "2024-03-15"))

        dao.deleteOldData("2024-03-13")

        assertThat(dao.getSessionCountByDate("2024-03-10")).isEqualTo(0)
        assertThat(dao.getSessionCountByDate("2024-03-15")).isEqualTo(1)
    }

    @Test
    fun getSessionsBetween_returnsSessionsInRange() = runTest {
        dao.insert(ScreenSession(startTime = 1L, endTime = 2L, durationMs = 100L, date = "2024-03-10"))
        dao.insert(ScreenSession(startTime = 3L, endTime = 4L, durationMs = 200L, date = "2024-03-12"))
        dao.insert(ScreenSession(startTime = 5L, endTime = 6L, durationMs = 300L, date = "2024-03-15"))

        val sessions = dao.getSessionsBetween("2024-03-11", "2024-03-14").first()
        assertThat(sessions).hasSize(1)
        assertThat(sessions[0].date).isEqualTo("2024-03-12")
    }
}
