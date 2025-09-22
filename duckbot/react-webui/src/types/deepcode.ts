/**
 * DeepCode Types and Interfaces
 *
 * This file contains comprehensive TypeScript types and interfaces
 * for the DeepCode AI code generation system integration.
 */

// Base interfaces
export interface DeepCodeResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: Date;
}

export interface DeepCodeJob {
  id: string;
  type: 'paper2code' | 'text2web' | 'text2backend';
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  title: string;
  description: string;
  progress: number;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
  estimatedDuration?: number; // in seconds
  output?: {
    files: GeneratedFile[];
    outputPath: string;
    downloadUrl?: string;
    preview?: string;
  };
  error?: string;
  config: any;
  metadata?: {
    modelUsed: string;
    tokensGenerated: number;
    processingTime: number;
    fileSize: number;
  };
}

export interface GeneratedFile {
  name: string;
  path: string;
  type: 'code' | 'config' | 'documentation' | 'asset' | 'test';
  language: string;
  size: number;
  content?: string;
  checksum?: string;
  dependencies?: string[];
}

// Paper2Code interfaces
export interface Paper2CodeInput {
  paper?: {
    title: string;
    authors: string[];
    abstract: string;
    content: string;
    url?: string;
    doi?: string;
    publishedAt?: Date;
  };
  file?: File | string;
  config: Paper2CodeConfig;
}

export interface Paper2CodeConfig {
  model: string;
  temperature: number;
  maxTokens: number;
  outputFormat: 'prototype' | 'production_ready' | 'research_implementation';
  includeTests: boolean;
  includeDocumentation: boolean;
  targetLanguage?: string;
  framework?: string;
  codeStyle: 'clean' | 'documented' | 'optimized' | 'minimal';
  complexity: 'basic' | 'intermediate' | 'advanced';
}

export interface Paper2CodeOutput {
  implementation: GeneratedFile[];
  documentation: GeneratedFile[];
  tests: GeneratedFile[];
  setupFiles: GeneratedFile[];
  examples: GeneratedFile[];
  readme?: string;
  executionGuide?: string;
  dependencies: string[];
  architecture: string;
}

// Text2Web interfaces
export interface Text2WebInput {
  description: string;
  config: Text2WebConfig;
}

export interface Text2WebConfig {
  framework: 'react' | 'vue' | 'angular' | 'svelte' | 'next' | 'nuxt';
  styling: 'css' | 'scss' | 'tailwind' | 'styled_components' | 'emotion';
  language: 'typescript' | 'javascript';
  features: WebAppFeatures;
  pages: PageConfig[];
  components: ComponentConfig[];
  integrations: IntegrationConfig[];
  deployment: DeploymentConfig;
}

export interface WebAppFeatures {
  auth: boolean;
  database: boolean;
  api: boolean;
  realTime: boolean;
  offline: boolean;
  responsive: boolean;
  pwa: boolean;
  seo: boolean;
  analytics: boolean;
  testing: boolean;
  documentation: boolean;
}

export interface PageConfig {
  name: string;
  path: string;
  type: 'static' | 'dynamic' | 'protected';
  components: string[];
  features: string[];
}

export interface ComponentConfig {
  name: string;
  type: 'ui' | 'layout' | 'form' | 'data' | 'utility';
  props: ComponentProp[];
  state?: ComponentState[];
}

export interface ComponentProp {
  name: string;
  type: string;
  required: boolean;
  description?: string;
  defaultValue?: any;
}

export interface ComponentState {
  name: string;
  type: string;
  initialValue?: any;
  persistence?: 'session' | 'local' | 'none';
}

export interface IntegrationConfig {
  type: 'api' | 'auth' | 'database' | 'storage' | 'analytics' | 'payment';
  provider: string;
  config: any;
}

export interface DeploymentConfig {
  platform: 'vercel' | 'netlify' | 'aws' | 'firebase' | 'docker' | 'static';
  config: any;
  environment?: Record<string, string>;
}

export interface Text2WebOutput {
  projectStructure: ProjectStructure;
  sourceFiles: GeneratedFile[];
  configuration: GeneratedFile[];
  documentation: GeneratedFile[];
  setupScripts: GeneratedFile[];
  deploymentFiles: GeneratedFile[];
  dependencies: PackageDependencies;
  buildCommands: string[];
  runCommands: string[];
}

// Text2Backend interfaces
export interface Text2BackendInput {
  description: string;
  config: Text2BackendConfig;
}

export interface Text2BackendConfig {
  architecture: 'monolithic' | 'microservices' | 'serverless' | 'event_driven';
  language: 'python' | 'javascript' | 'java' | 'go' | 'rust' | 'csharp';
  framework: string;
  database: DatabaseConfig;
  authentication: AuthConfig;
  api: ApiConfig;
  features: BackendFeatures;
  deployment: BackendDeploymentConfig;
}

export interface DatabaseConfig {
  type: 'postgresql' | 'mysql' | 'mongodb' | 'redis' | 'sqlite' | 'dynamodb';
  schema?: DatabaseSchema;
  migrations: boolean;
  orm?: boolean;
  ormType?: string;
  connectionConfig: any;
}

export interface DatabaseSchema {
  tables: TableSchema[];
  relationships: RelationshipSchema[];
  indexes: IndexSchema[];
}

export interface TableSchema {
  name: string;
  columns: ColumnSchema[];
  constraints: ConstraintSchema[];
}

export interface ColumnSchema {
  name: string;
  type: string;
  nullable: boolean;
  unique: boolean;
  default?: any;
  autoIncrement?: boolean;
  foreignKey?: ForeignKeySchema;
}

export interface ForeignKeySchema {
  table: string;
  column: string;
  onDelete?: 'cascade' | 'set_null' | 'restrict' | 'set_default';
  onUpdate?: 'cascade' | 'set_null' | 'restrict' | 'set_default';
}

export interface ConstraintSchema {
  type: 'primary_key' | 'unique' | 'check' | 'foreign_key';
  columns: string[];
  name?: string;
  condition?: string;
}

export interface RelationshipSchema {
  from: { table: string; column: string };
  to: { table: string; column: string };
  type: 'one_to_one' | 'one_to_many' | 'many_to_many';
  onDelete?: string;
  onUpdate?: string;
}

export interface IndexSchema {
  name: string;
  table: string;
  columns: string[];
  unique: boolean;
  type?: 'btree' | 'hash' | 'gin' | 'gist';
}

export interface AuthConfig {
  method: 'jwt' | 'oauth' | 'session' | 'basic' | 'api_key';
  providers?: AuthProvider[];
  middleware?: AuthMiddleware[];
  roles?: RoleConfig[];
  permissions?: PermissionConfig[];
}

export interface AuthProvider {
  name: string;
  config: any;
}

export interface AuthMiddleware {
  name: string;
  config: any;
}

export interface RoleConfig {
  name: string;
  permissions: string[];
  inherits?: string[];
}

export interface PermissionConfig {
  name: string;
  resource: string;
  actions: string[];
  conditions?: any;
}

export interface ApiConfig {
  type: 'rest' | 'graphql' | 'websocket' | 'grpc';
  version: string;
  endpoints: ApiEndpoint[];
  documentation: boolean;
  rateLimiting?: RateLimitConfig;
  caching?: CacheConfig;
}

export interface ApiEndpoint {
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  auth: boolean;
  validation?: ValidationSchema;
  handler: string;
  description?: string;
  tags?: string[];
}

export interface ValidationSchema {
  body?: any;
  params?: any;
  query?: any;
  headers?: any;
}

export interface RateLimitConfig {
  enabled: boolean;
  requests: number;
  window: number; // in seconds
  strategy: 'fixed_window' | 'sliding_window' | 'token_bucket';
}

export interface CacheConfig {
  enabled: boolean;
  type: 'memory' | 'redis' | 'memcached';
  ttl: number;
  strategy: 'cache_first' | 'cache_only' | 'no_cache';
}

export interface BackendFeatures {
  realtime: boolean;
  websocket: boolean;
  cron: boolean;
  queue: boolean;
  cache: boolean;
  logging: boolean;
  monitoring: boolean;
  testing: boolean;
  documentation: boolean;
}

export interface BackendDeploymentConfig {
  platform: 'docker' | 'aws' | 'gcp' | 'azure' | 'heroku' | 'render';
  config: any;
  environment?: Record<string, string>;
  ci_cd?: CICDConfig;
}

export interface CICDConfig {
  platform: 'github_actions' | 'gitlab_ci' | 'jenkins' | 'circleci';
  config: any;
  triggers: string[];
}

export interface Text2BackendOutput {
  architecture: GeneratedFile[];
  sourceFiles: GeneratedFile[];
  configuration: GeneratedFile[];
  database: GeneratedFile[];
  tests: GeneratedFile[];
  documentation: GeneratedFile[];
  deployment: GeneratedFile[];
  dependencies: PackageDependencies;
  setupScripts: GeneratedFile[];
  apiSpec?: GeneratedFile;
}

// Common interfaces
export interface ProjectStructure {
  directories: string[];
  files: ProjectFile[];
}

export interface ProjectFile {
  path: string;
  type: string;
  size: number;
  description?: string;
}

export interface PackageDependencies {
  dependencies: Record<string, string>;
  devDependencies: Record<string, string>;
  peerDependencies?: Record<string, string>;
  optionalDependencies?: Record<string, string>;
}

// Configuration interfaces
export interface DeepCodeConfig {
  server: ServerConfig;
  models: ModelConfig;
  security: SecurityConfig;
  performance: PerformanceConfig;
  integrations: IntegrationSettings;
  advanced: AdvancedConfig;
}

export interface ServerConfig {
  host: string;
  port: number;
  useHttps: boolean;
  timeout: number;
  maxRetries: number;
  retryDelay: number;
}

export interface ModelConfig {
  defaultModel: string;
  fallbackModel: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  topK: number;
  streaming: boolean;
  cacheEnabled: boolean;
}

export interface SecurityConfig {
  enableAuth: boolean;
  apiKeyRequired: boolean;
  rateLimiting: RateLimitConfig;
  corsEnabled: boolean;
  allowedOrigins: string[];
  enableLogging: boolean;
  logLevel: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
}

export interface PerformanceConfig {
  maxConcurrentJobs: number;
  jobTimeout: number;
  memoryLimitMb: number;
  cpuLimitPercent: number;
  enableCaching: boolean;
  cacheTtl: number;
  parallelProcessing: boolean;
  optimizationLevel: 'minimal' | 'balanced' | 'aggressive' | 'maximum';
}

export interface IntegrationSettings {
  github: GitHubConfig;
  gitlab: GitLabConfig;
  webhooks: WebhookConfig;
}

export interface GitHubConfig {
  enabled: boolean;
  token?: string;
  defaultBranch: string;
  autoCommit: boolean;
}

export interface GitLabConfig {
  enabled: boolean;
  token?: string;
  defaultBranch: string;
  autoCommit: boolean;
}

export interface WebhookConfig {
  enabled: boolean;
  secret?: string;
  allowedEvents: string[];
}

export interface AdvancedConfig {
  debugMode: boolean;
  enableTelemetry: boolean;
  customTemplatesDir: string;
  outputDir: string;
  tempCleanupInterval: number;
  maxLogFiles: number;
  logFileSizeMb: number;
}

// WebSocket interfaces
export interface DeepCodeWebSocketMessage {
  type: 'job_update' | 'progress' | 'error' | 'notification' | 'system_status';
  jobId?: string;
  data: any;
  timestamp: Date;
}

export interface JobUpdateMessage {
  jobId: string;
  status: string;
  progress: number;
  message?: string;
  error?: string;
}

export interface ProgressMessage {
  jobId: string;
  currentStep: string;
  stepProgress: number;
  totalSteps: number;
  estimatedTimeRemaining?: number;
}

// Error interfaces
export interface DeepCodeError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
  retryable: boolean;
}

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
  constraint: string;
}

// Event interfaces
export interface DeepCodeEvent {
  type: 'job_created' | 'job_started' | 'job_completed' | 'job_failed' | 'job_cancelled';
  jobId: string;
  timestamp: Date;
  data: any;
}

// Utility types
export type DeepCodeJobType = DeepCodeJob['type'];
export type DeepCodeJobStatus = DeepCodeJob['status'];
export type DeepCodeFileType = GeneratedFile['type'];

export type SupportedFramework =
  | 'react' | 'vue' | 'angular' | 'svelte'
  | 'next' | 'nuxt' | 'express' | 'fastapi'
  | 'django' | 'flask' | 'spring' | 'laravel';

export type SupportedLanguage =
  | 'typescript' | 'javascript' | 'python'
  | 'java' | 'go' | 'rust' | 'csharp'
  | 'php' | 'ruby' | 'swift' | 'kotlin';

export type SupportedDatabase =
  | 'postgresql' | 'mysql' | 'mongodb'
  | 'redis' | 'sqlite' | 'dynamodb';

// Helper types
export interface DeepCodeServiceOptions {
  baseUrl?: string;
  apiKey?: string;
  timeout?: number;
  retries?: number;
  enableWebSocket?: boolean;
  enableLogging?: boolean;
}

export interface UseDeepCodeOptions {
  autoConnect?: boolean;
  enableWebSocket?: boolean;
  pollInterval?: number;
  onError?: (error: DeepCodeError) => void;
  onSuccess?: (response: DeepCodeResponse) => void;
}

// Default configurations
export const DEFAULT_DEEPCODE_CONFIG: DeepCodeConfig = {
  server: {
    host: 'localhost',
    port: 8790,
    useHttps: false,
    timeout: 30000,
    maxRetries: 3,
    retryDelay: 1000
  },
  models: {
    defaultModel: 'qwen3-coder',
    fallbackModel: 'gpt-4',
    temperature: 0.2,
    maxTokens: 4000,
    topP: 0.9,
    topK: 50,
    streaming: true,
    cacheEnabled: true
  },
  security: {
    enableAuth: true,
    apiKeyRequired: false,
    rateLimiting: {
      enabled: true,
      requests: 60,
      window: 60,
      strategy: 'fixed_window'
    },
    corsEnabled: true,
    allowedOrigins: ['*'],
    enableLogging: true,
    logLevel: 'INFO'
  },
  performance: {
    maxConcurrentJobs: 5,
    jobTimeout: 300000,
    memoryLimitMb: 4096,
    cpuLimitPercent: 80,
    enableCaching: true,
    cacheTtl: 3600,
    parallelProcessing: true,
    optimizationLevel: 'balanced'
  },
  integrations: {
    github: {
      enabled: false,
      defaultBranch: 'main',
      autoCommit: false
    },
    gitlab: {
      enabled: false,
      defaultBranch: 'main',
      autoCommit: false
    },
    webhooks: {
      enabled: true,
      allowedEvents: ['job.completed', 'job.failed']
    }
  },
  advanced: {
    debugMode: false,
    enableTelemetry: false,
    customTemplatesDir: '',
    outputDir: './deepcode_output',
    tempCleanupInterval: 3600,
    maxLogFiles: 10,
    logFileSizeMb: 50
  }
};

// Validation schemas
export interface Paper2CodeValidationSchema {
  paper?: {
    title?: { required: boolean; minLength: number; maxLength: number };
    abstract?: { required: boolean; minLength: number; maxLength: number };
  };
  config: {
    model: { required: boolean; enum: string[] };
    temperature: { required: boolean; min: number; max: number };
    maxTokens: { required: boolean; min: number; max: number };
  };
}

export interface Text2WebValidationSchema {
  description: { required: boolean; minLength: number; maxLength: number };
  config: {
    framework: { required: boolean; enum: string[] };
    language: { required: boolean; enum: string[] };
    styling: { required: boolean; enum: string[] };
  };
}

export interface Text2BackendValidationSchema {
  description: { required: boolean; minLength: number; maxLength: number };
  config: {
    architecture: { required: boolean; enum: string[] };
    language: { required: boolean; enum: string[] };
    framework: { required: boolean };
  };
}