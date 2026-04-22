package com.phoneguardian.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.phoneguardian.data.local.dao.BatteryEventDao
import com.phoneguardian.data.local.dao.ChargeCycleDao
import com.phoneguardian.data.local.dao.DailySummaryDao
import com.phoneguardian.data.local.dao.ScreenSessionDao
import com.phoneguardian.data.local.entity.BatteryEvent
import com.phoneguardian.data.local.entity.ChargeCycle
import com.phoneguardian.data.local.entity.DailySummary
import com.phoneguardian.data.local.entity.ScreenSession

@Database(
    entities = [
        ScreenSession::class,
        BatteryEvent::class,
        DailySummary::class,
        ChargeCycle::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {

    abstract fun screenSessionDao(): ScreenSessionDao
    abstract fun batteryEventDao(): BatteryEventDao
    abstract fun dailySummaryDao(): DailySummaryDao
    abstract fun chargeCycleDao(): ChargeCycleDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "phone_guardian_db"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
