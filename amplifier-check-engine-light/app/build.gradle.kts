plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp")
}

android {
    namespace = "com.amplifierhealth.checkenginelight"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.amplifierhealth.checkenginelight"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0-phase1"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    buildFeatures {
        compose = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.06.00")
    implementation(composeBom)

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.4")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.4")
    implementation("androidx.activity:activity-compose:1.9.1")

    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.navigation:navigation-compose:2.7.7")

    // Scheduling / background work.
    implementation("androidx.work:work-runtime-ktx:2.9.1")

    // Local persistence: results + history metadata.
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")

    // Settings / small key-value state (onboarding complete, notification window).
    implementation("androidx.datastore:datastore-preferences:1.1.1")

    // Encrypted temp storage for the raw clip between recording and upload.
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    // Network layer to the Supabase proxy in front of the LAM API.
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.1")
    // DecryptingRequestBody streams via Okio's Sink/Source directly, so this
    // needs to be an explicit dependency rather than relying on OkHttp's own
    // (implementation-scoped) transitive copy.
    implementation("com.squareup.okio:okio:3.9.0")

    testImplementation("junit:junit:4.13.2")
}
