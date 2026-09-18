package com.amplifierhealth.checkenginelight.data.local

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow
import java.time.LocalDate

@Dao
interface DailyCheckDao {

    @Upsert
    suspend fun upsert(entity: DailyCheckEntity)

    @Query("SELECT * FROM daily_checks WHERE localDate = :date LIMIT 1")
    suspend fun getForDate(date: LocalDate): DailyCheckEntity?

    @Query("SELECT * FROM daily_checks ORDER BY localDate DESC LIMIT 1")
    fun observeLatest(): Flow<DailyCheckEntity?>

    @Query("SELECT * FROM daily_checks ORDER BY localDate DESC LIMIT :limit")
    fun observeHistory(limit: Int = 90): Flow<List<DailyCheckEntity>>
}
