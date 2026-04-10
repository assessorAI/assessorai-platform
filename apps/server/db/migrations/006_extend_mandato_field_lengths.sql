-- Extend mandato field lengths to accommodate longer values
-- Migration 006: Extend field lengths for mandatos table

-- Extend casa_legislativa from 50 to 100 characters
ALTER TABLE mandatos ALTER COLUMN casa_legislativa TYPE VARCHAR(100);

-- Extend nome_parlamentar from 50 to 100 characters for safety
ALTER TABLE mandatos ALTER COLUMN nome_parlamentar TYPE VARCHAR(100);

-- Extend cargo_parlamentar from 50 to 100 characters
ALTER TABLE mandatos ALTER COLUMN cargo_parlamentar TYPE VARCHAR(100);

-- Extend partido from 50 to 100 characters
ALTER TABLE mandatos ALTER COLUMN partido TYPE VARCHAR(100);

-- Extend municipio from 50 to 100 characters
ALTER TABLE mandatos ALTER COLUMN municipio TYPE VARCHAR(100);

-- Extend esfera from 50 to 100 characters
ALTER TABLE mandatos ALTER COLUMN esfera TYPE VARCHAR(100);
