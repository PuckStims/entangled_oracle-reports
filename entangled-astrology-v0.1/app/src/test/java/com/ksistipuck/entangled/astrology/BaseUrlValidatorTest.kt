package com.ksistipuck.entangled.astrology

import com.ksistipuck.entangled.astrology.core.repository.BaseUrlValidator
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BaseUrlValidatorTest {
    @Test fun acceptsHttpAndHttpsUrls() {
        assertTrue(BaseUrlValidator.isValid("http://10.0.2.2:8000"))
        assertTrue(BaseUrlValidator.isValid("https://oracle.example.com"))
    }

    @Test fun rejectsBlankAndUnschemedUrls() {
        assertFalse(BaseUrlValidator.isValid(""))
        assertFalse(BaseUrlValidator.isValid("localhost:8000"))
        assertFalse(BaseUrlValidator.isValid("https://bad url.test"))
    }
}
