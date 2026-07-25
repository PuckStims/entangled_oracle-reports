package com.ksistipuck.entangled.astrology.core.validation

import com.ksistipuck.entangled.astrology.core.model.CurrentField
import com.ksistipuck.entangled.astrology.core.model.Provenance

class ContractViolation(message: String) : IllegalStateException(message)

object EngineResponseValidator {
    fun validateCurrentField(field: CurrentField): CurrentField {
        requireText(field.fieldId, "fieldId")
        requireText(field.calculatedAt, "calculatedAt")
        requireText(field.timeZone, "timeZone")
        validateProvenance(field.provenance)

        val eventIds = field.events.map { it.id }.toSet()
        if (eventIds.size != field.events.size) throw ContractViolation("Current field contains duplicate event IDs.")

        field.events.forEach { event ->
            requireText(event.id, "events[].id")
            requireText(event.technique, "events[].technique")
            requireText(event.natalTarget, "events[].natalTarget")
            requireText(event.phase, "events[].phase")
            if (event.phase !in setOf("applying", "exact", "separating", "background")) {
                throw ContractViolation("Unsupported event phase: ${event.phase}")
            }
        }

        field.patterns.forEach { pattern ->
            requireText(pattern.title, "patterns[].title")
            requireText(pattern.summary, "patterns[].summary")
            if (pattern.eventIds.isEmpty()) throw ContractViolation("Pattern ${pattern.id} has no supporting event IDs.")
            val missing = pattern.eventIds.filterNot(eventIds::contains)
            if (missing.isNotEmpty()) throw ContractViolation("Pattern ${pattern.id} references missing events: $missing")
        }
        return field
    }

    fun validateProvenance(provenance: Provenance) {
        requireText(provenance.engineVersion, "provenance.engineVersion")
        requireText(provenance.schemaVersion, "provenance.schemaVersion")
        if (provenance.calculationModules.isEmpty()) {
            throw ContractViolation("provenance.calculationModules cannot be empty.")
        }
    }

    private fun requireText(value: String, field: String) {
        if (value.isBlank()) throw ContractViolation("$field cannot be blank.")
    }
}
