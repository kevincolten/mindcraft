import * as Mindcraft from './src/mindcraft/mindcraft.js';
import settings from './settings.js';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import { readFileSync } from 'fs';
import { findLMStudio } from './src/mindcraft/discovery.js';

function parseArguments() {
    return yargs(hideBin(process.argv))
        .option('profiles', {
            type: 'array',
            describe: 'List of agent profile paths',
        })
        .option('task_path', {
            type: 'string',
            describe: 'Path to task file to execute'
        })
        .option('task_id', {
            type: 'string',
            describe: 'Task ID to execute'
        })
        .help()
        .alias('help', 'h')
        .parse();
}
const args = parseArguments();
if (args.profiles) {
    settings.profiles = args.profiles;
}
if (args.task_path) {
    let tasks = JSON.parse(readFileSync(args.task_path, 'utf8'));
    if (args.task_id) {
        settings.task = tasks[args.task_id];
        settings.task.task_id = args.task_id;
    }
    else {
        throw new Error('task_id is required when task_path is provided');
    }
}

// these environment variables override certain settings
if (process.env.MINECRAFT_HOST) {
    settings.host = process.env.MINECRAFT_HOST;
}
if (process.env.MINECRAFT_PORT) {
    settings.port = process.env.MINECRAFT_PORT;
}
if (process.env.MINDSERVER_PORT) {
    settings.mindserver_port = process.env.MINDSERVER_PORT;
}
if (process.env.PROFILES && JSON.parse(process.env.PROFILES).length > 0) {
    settings.profiles = JSON.parse(process.env.PROFILES);
}
if (process.env.INSECURE_CODING) {
    settings.allow_insecure_coding = true;
}
if (process.env.BLOCKED_ACTIONS) {
    settings.blocked_actions = JSON.parse(process.env.BLOCKED_ACTIONS);
}
if (process.env.MAX_MESSAGES) {
    settings.max_messages = process.env.MAX_MESSAGES;
}
if (process.env.NUM_EXAMPLES) {
    settings.num_examples = process.env.NUM_EXAMPLES;
}
if (process.env.LOG_ALL) {
    settings.log_all_prompts = process.env.LOG_ALL;
}
if (process.env.SETTINGS_JSON) {
    try {
        Object.assign(settings, JSON.parse(process.env.SETTINGS_JSON));
    } catch (err) {
        console.error("Failed to parse environment variable for SETTINGS_JSON:", err);
    }
}

Mindcraft.init(false, settings.mindserver_port, settings.auto_open_ui);

// Resolve the LLM endpoint once: explicit env var wins, otherwise scan the LAN for LM Studio.
let llmUrl = process.env.LLM_URL || null;
if (!llmUrl) {
    llmUrl = await findLMStudio(process.env.LLM_PORT ? Number(process.env.LLM_PORT) : 1234);
    if (!llmUrl) {
        console.error('No LLM_URL set and LM Studio was not found on the LAN. Set LLM_URL explicitly to continue.');
        process.exit(1);
    }
}
const llmModel = process.env.LLM_MODEL || 'andy-4';
const embeddingModel = process.env.EMBEDDING_MODEL || 'text-embedding-embeddinggemma-300m';

for (let profile of settings.profiles) {
    const profile_json = JSON.parse(readFileSync(profile, 'utf8'));
    // fill in model/embedding config if the profile leaves it blank
    if (profile_json.model && !profile_json.model.url) {
        profile_json.model.api = 'openai';
        profile_json.model.url = llmUrl;
        profile_json.model.model = llmModel;
    }
    if (profile_json.embedding && !profile_json.embedding.url) {
        profile_json.embedding.api = 'openai';
        profile_json.embedding.url = llmUrl;
        profile_json.embedding.model = embeddingModel;
    }
    settings.profile = profile_json;
    Mindcraft.createAgent(settings);
}
