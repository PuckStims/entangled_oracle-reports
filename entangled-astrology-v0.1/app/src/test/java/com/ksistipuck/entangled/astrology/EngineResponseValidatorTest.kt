package com.ksistipuck.entangled.astrology

import com.ksistipuck.entangled.astrology.core.model.*
import com.ksistipuck.entangled.astrology.core.validation.ContractViolation
import com.ksistipuck.entangled.astrology.core.validation.EngineResponseValidator
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class EngineResponseValidatorTest {
    @Test fun acceptsPatternWhoseEvidenceIsPresent() {
        val field = validField()
        assertEquals(field, EngineResponseValidator.validateCurrentField(field))
    }

    @Test fun rejectsPatternsWithoutSupportingEvents() {
        val field = validField().copy(
            patterns = listOf(FieldPattern("p1", "Title", "Summary", "dominant", "peak", listOf("missing"))),
            events = emptyList(),
        )
        assertThrows(ContractViolation::class.java) { EngineResponseValidator.validateCurrentField(field) }
    }

    @Test fun rejectsDuplicateEventIds() {
        val original = validField()
        val field = original.copy(events = original.events + original.events.first())
        assertThrows(ContractViolation::class.java) { EngineResponseValidator.validateCurrentField(field) }
    }

    @Test fun rejectsUnknownEventPhase() {
        val original = validField()
        val field = original.copy(events = listOf(original.events.first().copy(phase = "mysterious")))
        assertThrows(ContractViolation::class.java) { EngineResponseValidator.validateCurrentField(field) }
    }

    private fun validField(): CurrentField {
        val event = CalculatedEvent(
            id = "event-1",
            technique = "transit",
            movingBody = "Mars",
            natalTarget = "Descendant",
            aspect = "trine",
            orbDegrees = 0.42,
            phase = "applying",
            exactAt = "2026-07-18T23:14:00Z",
            birthTimeSensitive = true,
        )
        return CurrentField(
            fieldId = "field-1",
            calculatedAt = "2026-07-18T12:00:00Z",
            timeZone = "America/Chicago",
            windowStart = "2026-07-18T00:00:00-05:00",
            windowEnd = "2026-07-19T00:00:00-05:00",
            patterns = listOf(FieldPattern("p1", "Title", "Summary", "dominant", "peak", listOf(event.id))),
            events = listOf(event),
            provenance = Provenance("0.1", "1.0", listOf("engine.transit_engine"), true),
        )
    }
}
