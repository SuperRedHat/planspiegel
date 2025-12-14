import { IStep } from '@app/interfaces/check';
import CheckContent from './CheckContent';

export default function URLChecksList({ steps }: { steps: IStep[] }) {
  return (
    <ul role='list' className='space-y-3 pt-6'>
      {steps?.map((item) => (
        <li
          key={item.tag}
          id={item.tag}
          className='overflow-hidden bg-white min-h-20 px-4 py-4 shadow print:shadow-none sm:rounded-md sm:px-6 break-before-page'
        >
          <CheckContent
            chat_id={item.chat?.chat_id}
            checkup_id={item?.checkup_id}
            check_id={item.chat?.check_id}
            item={item}
          />
        </li>
      ))}
    </ul>
  );
}
