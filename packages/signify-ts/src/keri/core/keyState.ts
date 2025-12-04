import { components } from '../../types/keria-api-schema.ts';

export type KeyState = components['schemas']['KeyStateRecord'];

export type EstablishmentState = components['schemas']['StateEERecord'];

/**
 * Marker interface for state configuring an IdentifierManager.
 */
// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface IdentifierManagerState {}

/**
 * Defining configuration parameters for a specified, deterministic salt of an IdentifierManager.
 */
export type SaltyKeyState = components['schemas']['SaltyState'];

/**
 * Defining configuration parameters for a random seed identifier manager.
 */
export type RandyKeyState = components['schemas']['RandyKeyState'];

/**
 * Defining properties a multi-signature group identifier manager.
 */
export type GroupKeyState = components['schemas']['GroupKeyState'];

/**
 * Defining properties for an external module identifier manager that uses externally managed keys such as in an HSM or a KMS system.
 */
export type ExternState = components['schemas']['ExternState'];

/**
 * Defining properties of an identifier habitat, know as a Hab in KERIpy.
 */
export type HabState = components['schemas']['Identifier'];
