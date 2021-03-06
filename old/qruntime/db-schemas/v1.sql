CREATE TABLE `version`
(
 `version` INTEGER -- contains one row, set to 1
);

CREATE TABLE `node` -- contains one row
(
 `webport` STRING,
 `pubkey` STRING, -- "pk0-base32..", nacl public key
 `privkey` STRING -- "sk0-base32..", nacl private key
);

CREATE TABLE `webui_initial_nonces`
(
 `nonce` STRING
);

CREATE TABLE `webui_access_tokens`
(
 `token` STRING
);

CREATE TABLE `vat_urls`
(
 `vatid` VARCHAR(256), -- "pk0-base32.."
 `url` VARCHAR(512)
);

CREATE TABLE `outbound_msgnums`
(
 `to_vatid` VARCHAR(256) UNIQUE, -- "pk0-base32.."
 `next_msgnum` INTEGER -- one higher than last ACKed message
);

CREATE TABLE `outbound_messages` -- unACKed messages
(
 `to_vatid` STRING, -- "pk0-base32.."
 `last_sent` INTEGER, -- seconds since epoch
 `msgnum` INTEGER,
 `message_b64` STRING -- boxed and ready to ship
);

CREATE TABLE `inbound_msgnums`
(
 `from_vatid` VARCHAR(256) UNIQUE, -- "pk0-base32.."
 `next_msgnum` INTEGER -- one higher than last checkpointed message
);

CREATE TABLE `inbound_messages` -- undelivered messages
(
 `from_vatid` STRING, -- "pk0-base32.."
 `msgnum` INTEGER,
 `message_json` STRING -- decrypted
);

CREATE TABLE `memory`
(
 `memid` VARCHAR(256) UNIQUE, -- "mem0-base32.."
 `data_json` STRING
);

CREATE TABLE `power`
(
 `powid` VARCHAR(256) UNIQUE, -- "pow0-base32.."
 `power_json` STRING
);

CREATE TABLE `urbjects`
(
 `urbjid` VARCHAR(256) UNIQUE, -- "urb0-base32.."
 `powid` VARCHAR(256), -- "pow0-base32.."
 `code` STRING
);
