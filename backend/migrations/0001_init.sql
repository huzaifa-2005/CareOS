-- Required for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Clinics (tenant root)
CREATE TABLE clinics (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    timezone text NOT NULL DEFAULT 'Asia/Karachi',
    whatsapp_number text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 2. Clinic staff (dashboard logins)
CREATE TABLE clinic_staff (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id uuid NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    full_name text NOT NULL,
    email text UNIQUE NOT NULL,
    role text NOT NULL CHECK (role IN ('owner', 'receptionist')),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 3. Doctors
CREATE TABLE doctors (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id uuid NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    full_name text NOT NULL,
    specialty text,
    consultation_fee numeric(10,2),
    is_active boolean NOT NULL DEFAULT true
);

-- 4. Patients
CREATE TABLE patients (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id uuid NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    full_name text,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 5. Contact identifiers (multi-channel identity)
CREATE TABLE contact_identifiers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    channel text NOT NULL CHECK (channel IN ('whatsapp', 'web')),
    identifier_value text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (channel, identifier_value)
);

-- 6. Appointments
CREATE TABLE appointments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id uuid NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id uuid REFERENCES doctors(id),
    treatment_type text,
    urgency_level text NOT NULL DEFAULT 'normal' CHECK (urgency_level IN ('normal', 'urgent')),
    budget_range text,
    scheduled_at timestamptz NOT NULL,
    status text NOT NULL DEFAULT 'booked' CHECK (status IN ('booked', 'completed', 'no_show', 'cancelled', 'rescheduled')),
    is_walkin boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 7. Payments
CREATE TABLE payments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id uuid NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    provider text NOT NULL CHECK (provider IN ('jazzcash', 'easypaisa')),
    amount numeric(10,2) NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'expired')),
    payment_link text,
    expires_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 8. Conversations
CREATE TABLE conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id uuid NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    channel text NOT NULL,
    message_direction text NOT NULL CHECK (message_direction IN ('inbound', 'outbound')),
    message_text text NOT NULL,
    intent_route text CHECK (intent_route IN ('rule_based', 'rag_llm')),
    is_flagged_for_review boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 9. Scheduled messages (Celery-driven)
CREATE TABLE scheduled_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id uuid NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    message_type text NOT NULL CHECK (message_type IN ('reminder_24h', 'reminder_2h', 'follow_up', 'no_show_recovery')),
    send_at timestamptz NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 10. FAQs (RAG source of truth)
CREATE TABLE faqs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id uuid NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    question text NOT NULL,
    answer text NOT NULL,
    category text CHECK (category IN ('timings', 'fees', 'doctors', 'directions', 'other')),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Helpful indexes for common lookups
CREATE INDEX idx_patients_clinic ON patients(clinic_id);
CREATE INDEX idx_appointments_clinic ON appointments(clinic_id);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_conversations_clinic ON conversations(clinic_id);
CREATE INDEX idx_conversations_patient ON conversations(patient_id);
CREATE INDEX idx_faqs_clinic ON faqs(clinic_id);
CREATE INDEX idx_scheduled_messages_send_at ON scheduled_messages(send_at) WHERE status = 'pending';