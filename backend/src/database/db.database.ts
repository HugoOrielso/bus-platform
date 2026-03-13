import { PrismaClient } from "../generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL!,
});

const prismaClient = new PrismaClient({ adapter });

export type PrismaClientType = typeof prismaClient;
export const prisma: PrismaClientType = prismaClient;