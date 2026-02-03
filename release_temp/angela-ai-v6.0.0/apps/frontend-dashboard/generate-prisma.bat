@echo off
echo Generating Prisma client...
npx prisma generate
echo Pushing database schema...
npx prisma db push
echo Done!
pause