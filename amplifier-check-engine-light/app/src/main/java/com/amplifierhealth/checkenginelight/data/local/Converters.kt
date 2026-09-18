package com.amplifierhealth.checkenginelight.data.local

import androidx.room.TypeConverter
import java.time.LocalDate

class Converters {
    @TypeConverter
    fun fromLocalDate(date: LocalDate): String = date.toString()

    @TypeConverter
    fun toLocalDate(value: String): LocalDate = LocalDate.parse(value)

    @TypeConverter
    fun fromCheckStatus(status: CheckStatus): String = status.name

    @TypeConverter
    fun toCheckStatus(value: String): CheckStatus = CheckStatus.valueOf(value)
}
