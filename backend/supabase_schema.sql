-- Supabase schema for persistent dedup + job history.
-- Run in the Supabase SQL editor (or `supabase db push`).

create table if not exists public.companies (
  id bigint generated always as identity primary key,
  dedup_key text unique not null,
  name text,
  phone text,
  email text,
  website text,
  street text,
  house_number text,
  postal_code text,
  city text,
  state text,
  country text default 'DE',
  category text,
  source text,
  source_url text,
  found_at timestamptz default now()
);

create table if not exists public.jobs (
  id bigint primary key,
  status text not null default 'running',
  city_count int default 0,
  category_count int default 0,
  total_found int default 0,
  total_added int default 0,
  total_duplicates int default 0,
  total_merged int default 0,
  total_failed int default 0,
  created_at timestamptz default now(),
  completed_at timestamptz
);

create table if not exists public.job_companies (
  job_id bigint not null references public.jobs(id) on delete cascade,
  company_id bigint not null references public.companies(id) on delete cascade,
  primary key (job_id, company_id)
);

create index if not exists ix_companies_website on public.companies(website);
create index if not exists ix_companies_phone on public.companies(phone);
create index if not exists ix_companies_email on public.companies(email);
create index if not exists ix_job_companies_job on public.job_companies(job_id);

alter table public.companies enable row level security;
alter table public.jobs enable row level security;
alter table public.job_companies enable row level security;

-- Allow service role (and anon if you expose it) to read/write.
create policy "service read companies" on public.companies for select using (true);
create policy "service insert companies" on public.companies for insert with check (true);
create policy "service update companies" on public.companies for update using (true);
create policy "service read jobs" on public.jobs for select using (true);
create policy "service insert jobs" on public.jobs for insert with check (true);
create policy "service update jobs" on public.jobs for update using (true);
create policy "service read job_companies" on public.job_companies for select using (true);
create policy "service insert job_companies" on public.job_companies for insert with check (true);