# Entangled ecosystem linking

The ecosystem switcher is backed by `EntangledAppRegistry`. Each destination has a stable internal identifier, consumer label, description, current-app flag, and optional launch URI.

A destination with no verified URI remains visibly unavailable. Do not insert temporary marketing URLs or guess Android package names.

When another Entangled application is ready:

1. Establish an HTTPS Android App Link where possible.
2. Verify domain ownership and intent filters in the destination app.
3. Add the verified URI to `EntangledAppRegistry`.
4. Test installed-app launch, browser fallback, inaccessible destination, and return navigation.
5. Keep each divination practice visually related but semantically distinct.
